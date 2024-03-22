"""Generate XML Schema Definition (XSD) corresponding to the meta-model."""

import re
import xml.etree.ElementTree as ET

# noinspection PyUnresolvedReferences
import xml.dom.minidom
from typing import TextIO, MutableMapping, Optional, Tuple, List, Sequence, Any

from icontract import ensure, require
import greenery

import aas_core_codegen.xsd
from aas_core_codegen import (
    naming,
    specific_implementations,
    intermediate,
    run,
    infer_for_schema,
)
from aas_core_codegen.common import Error, assert_never, Identifier
from aas_core_codegen.xsd import naming as xsd_naming
from aas_core_codegen.parse import retree as parse_retree

assert aas_core_codegen.xsd.__doc__ == __doc__


def _define_for_enumeration(enumeration: intermediate.Enumeration) -> List[ET.Element]:
    """
    Generate the definitions for an ``enumeration``.
    The root element is to be *extended* with the resulting list.
    """
    restriction = ET.Element("xs:restriction", {"base": "xs:string"})
    for literal in enumeration.literals:
        restriction.append(ET.Element("xs:enumeration", {"value": literal.value}))

    element = ET.Element(
        "xs:simpleType", {"name": xsd_naming.type_name(enumeration.name)}
    )
    element.append(restriction)

    return [element]


_PRIMITIVE_MAP = {
    intermediate.PrimitiveType.BOOL: "xs:boolean",
    intermediate.PrimitiveType.INT: "xs:long",
    intermediate.PrimitiveType.FLOAT: "xs:double",
    intermediate.PrimitiveType.STR: "xs:string",
    intermediate.PrimitiveType.BYTEARRAY: "xs:base64Binary",
}
assert all(literal in _PRIMITIVE_MAP for literal in intermediate.PrimitiveType)

# noinspection RegExpSimplifiable
_ESCAPE_BACKSLASH_X_RE = re.compile(r"\\x([a-fA-f0-9]{2})")


def _undo_escaping_backslash_x_in_pattern(pattern: str) -> str:
    """
    Undo the escaping of `\\x??` in the ``pattern``.

    This is necessary since XML Schema Validators do not know how to handle such escape
    sequences in the patterns and need the verbatim characters.
    """
    parts = []  # type: List[str]
    cursor = None  # type: Optional[int]
    for mtch in re.finditer(_ESCAPE_BACKSLASH_X_RE, pattern):
        if cursor is None:
            parts.append(pattern[: mtch.start()])
        else:
            parts.append(pattern[cursor : mtch.start()])

        ascii_code = int(mtch.group(1), base=16)
        character = chr(ascii_code)
        parts.append(character)
        cursor = mtch.end()

    if cursor is None:
        parts.append(pattern)
    else:
        if cursor < len(pattern):
            parts.append(pattern[cursor:])

    return "".join(parts)


# noinspection RegExpSimplifiable
_ESCAPE_BACKSLASH_X_U_U_RE = re.compile(
    r"(\\x([a-fA-f0-9]{2})|\\u([a-fA-f0-9]{4})|\\U([a-fA-f0-9]{8}))"
)


def _undo_escaping_backslash_x_u_and_U_in_pattern(pattern: str) -> str:
    """
    Undo the escaping of ``\\x??``, ``\\u????`` and ``\\U????????`` in the ``pattern``.

    This is necessary since Greenery does not know how to handle such escape
    sequences in the patterns and need the verbatim characters.
    """
    parts = []  # type: List[str]
    cursor = None  # type: Optional[int]
    for mtch in re.finditer(_ESCAPE_BACKSLASH_X_U_U_RE, pattern):
        if cursor is None:
            parts.append(pattern[: mtch.start()])
        else:
            parts.append(pattern[cursor : mtch.start()])

        substring = mtch.group(0)
        assert len(substring) > 2
        assert substring[0] == "\\"

        hex_code = substring[2:]
        code_point = int(hex_code, base=16)
        character = chr(code_point)
        parts.append(character)
        cursor = mtch.end()

    if cursor is None:
        parts.append(pattern)
    else:
        if cursor < len(pattern):
            parts.append(pattern[cursor:])

    return "".join(parts)


class _AnchorRemover(parse_retree.BaseVisitor):
    """
    Remove anchors from a regex in-place.

    We need to remove the anchors (``^``, ``$``) since patterns in the XSD are always
    anchored.

    This is necessary since otherwise the schema validation fails.
    See: https://stackoverflow.com/questions/4367914/regular-expression-in-xml-schema-definition-fails
    """

    def visit_concatenation(self, node: parse_retree.Concatenation) -> None:
        """Visit the ``concatenation``."""
        new_concatenants = []  # type: List[parse_retree.Term]
        for concatenant in node.concatenants:
            if not (
                isinstance(concatenant.value, parse_retree.Symbol)
                and concatenant.value.kind
                in (parse_retree.SymbolKind.START, parse_retree.SymbolKind.END)
            ):
                new_concatenants.append(concatenant)

        node.concatenants = new_concatenants
        for concatenant in new_concatenants:
            self.visit(concatenant)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _translate_pattern(pattern: str) -> Tuple[Optional[str], Optional[str]]:
    """Translate the pattern to obtain the equivalent in XSD."""
    pattern = _undo_escaping_backslash_x_in_pattern(pattern)

    parsed, error = parse_retree.parse(values=[pattern])
    if error is not None:
        regex_line, pointer_line = parse_retree.render_pointer(error.cursor)
        return None, f"{error.message}\n{regex_line}\n{pointer_line}"
    assert parsed is not None

    remover = _AnchorRemover()
    remover.visit(parsed)

    values = parse_retree.render(regex=parsed)
    parts = []  # type: List[str]
    for value in values:
        assert isinstance(value, str), (
            "Only strings expected when rendering a pattern "
            "supplied originally as a string"
        )
        parts.append(value)

    return "".join(parts), None


def _generate_xs_restriction(
    base_type: intermediate.PrimitiveType,
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
) -> Tuple[Optional[ET.Element], Optional[str]]:
    """
    Generate the ``xs:restriction`` for the given primitive.

    Return the restriction element (if any length or pattern constraints), or
    an error.
    """
    if len_constraint is None and (
        pattern_constraints is None or (len(pattern_constraints) == 0)
    ):
        return None, None

    restriction = ET.Element("xs:restriction", {"base": _PRIMITIVE_MAP[base_type]})

    # NOTE (mristin, 2023-02-27):
    # We skip the general XML character pattern. It makes greenery
    # unbearably slow since it instantiates *each* character in
    # the character range. Since XML engines can not deal with the special
    # characters any ways, there is no need to include this constraint in
    # the XSD pattern restrictions.
    patterns_relevant_for_xsd: Optional[List[infer_for_schema.PatternConstraint]] = None

    if pattern_constraints is not None:
        patterns_relevant_for_xsd = [
            pattern_constraint
            for pattern_constraint in pattern_constraints
            if pattern_constraint.pattern
            != (
                "^[\\x09\\x0A\\x0D\\x20-\\uD7FF\\uE000-\\uFFFD"
                "\\U00010000-\\U0010FFFF]*$"
            )
        ]

    if patterns_relevant_for_xsd is not None and len(patterns_relevant_for_xsd) > 0:
        translated_pattern: Optional[str]

        if len(patterns_relevant_for_xsd) == 1:
            translated_pattern, error = _translate_pattern(
                patterns_relevant_for_xsd[0].pattern
            )
            if error is not None:
                return None, error
        else:
            # NOTE (mristin, 2023-02-27):
            # The module ``greenery`` is not annotated with types at the moment.
            merger = None  # type: Optional[Any]
            for pattern_constraint in patterns_relevant_for_xsd:
                # NOTE (mristin, 2023-02-27):
                # Greenery expects the characters to be in unicode and not escaped.
                translated_for_greenery = _undo_escaping_backslash_x_u_and_U_in_pattern(
                    pattern_constraint.pattern
                )

                try:
                    parsed = greenery.parse(translated_for_greenery)
                except Exception as exception:
                    if translated_for_greenery == pattern_constraint.pattern:
                        return None, (
                            f"The greenery failed to parse "
                            f"the pattern {translated_for_greenery!r}: {exception}"
                        )
                    else:
                        return None, (
                            f"The greenery failed to parse "
                            f"the pattern {translated_for_greenery!r} "
                            f"(which was originally {pattern_constraint.pattern!r}): "
                            f"{exception}"
                        )

                if merger is None:
                    merger = parsed
                else:
                    merger = merger & parsed

            assert merger is not None

            translated_pattern, error = _translate_pattern(str(merger))
            if error is not None:
                return None, error

        assert translated_pattern is not None

        pattern = ET.Element(
            "xs:pattern",
            {"value": translated_pattern},
        )

        restriction.append(pattern)

    if len_constraint is not None:
        if len_constraint.min_value is not None:
            min_length = ET.Element(
                "xs:minLength", {"value": str(len_constraint.min_value)}
            )
            restriction.append(min_length)

        if len_constraint.max_value is not None:
            max_length = ET.Element(
                "xs:maxLength", {"value": str(len_constraint.max_value)}
            )
            restriction.append(max_length)

    return restriction, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_xs_element_for_a_primitive_property(
    prop: intermediate.Property,
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
) -> Tuple[Optional[ET.Element], Optional[Error]]:
    """
    Generate the ``xs:element`` for a primitive property.

    A primitive property is a property whose type is either a primitive or
    a constrained primitive. The reason why we take these two together is that we
    in-line the constraints for the constrained primitives.

    We do not define the constrained primitives separately in the schema in order to
    avoid the confusion during comparisons between the XSD and the meta-model in
    the book.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and type_anno.our_type.name == "Value_data_type"
    ):
        # NOTE (mristin, 2022-11-10):
        # Please see :py:const:`_EXPLANATION_ABOUT_WHY_WE_EXPECT_VALUE_DATA_TYPE`
        # for the explanation why we hard-wire the ``Value_data_type`` here
        return (
            ET.Element(
                "xs:element",
                {
                    "name": naming.xml_property(prop.name),
                    "type": "valueDataType",
                },
            ),
            None,
        )

    # NOTE (mristin, 2022-03-30):
    # Specify the type of the ``type_anno`` here with assert instead of specifying it
    # in the pre-condition to help mypy a bit.

    base_type = intermediate.try_primitive_type(type_anno)

    assert (
        base_type is not None
    ), f"Expected a primitive or a constrained primitive, but got: {type_anno}"

    xs_restriction, error = _generate_xs_restriction(
        base_type=base_type,
        len_constraint=len_constraint,
        pattern_constraints=pattern_constraints,
    )
    if error is not None:
        return None, Error(
            prop.parsed.node,
            f"Failed to generate the restriction for property {prop.name}: {error}",
        )
    # NOTE (mristin, 2022-06-18):
    # xs_restriction may be None here if there are no constraints.

    xs_element: ET.Element

    if xs_restriction is None:
        xs_element = ET.Element(
            "xs:element",
            {
                "name": naming.xml_property(prop.name),
                "type": _PRIMITIVE_MAP[base_type],
            },
        )
    else:
        xs_simple_type = ET.Element("xs:simpleType")
        xs_simple_type.append(xs_restriction)

        xs_element = ET.Element("xs:element", {"name": naming.xml_property(prop.name)})
        xs_element.append(xs_simple_type)

    return xs_element, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_xs_element_for_a_list_property(
    prop: intermediate.Property,
    len_constraint: Optional[infer_for_schema.LenConstraint],
) -> Tuple[Optional[ET.Element], Optional[Error]]:
    """Generate the ``xs:element`` for a list property."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    # NOTE (mristin, 2022-03-30):
    # Specify the ``type_anno`` here with assert instead of specifying it
    # in the pre-condition to help mypy a bit
    assert isinstance(type_anno, intermediate.ListTypeAnnotation)

    min_occurs = "0"
    max_occurs = "unbounded"
    if len_constraint is not None:
        if len_constraint.min_value is not None:
            min_occurs = str(len_constraint.min_value)

        if len_constraint.max_value is not None:
            max_occurs = str(len_constraint.max_value)

    xs_element: ET.Element

    if isinstance(type_anno.items, intermediate.OurTypeAnnotation):
        # NOTE (mristin, 2021-11-13):
        # We need to nest the elements in the tag element to separate them in the
        # sequence.

        our_type = type_anno.items.our_type

        if isinstance(our_type, intermediate.Enumeration):
            return None, Error(
                prop.parsed.node,
                f"We do not know how to specify the list of enumerations "
                f"for the property {prop.name!r} of {prop.specified_for.name!r} "
                f"in the XSD with the type: {type_anno}",
            )

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            return None, Error(
                prop.parsed.node,
                f"We do not know how to specify the list of constrained primitives "
                f"for the property {prop.name!r} of {prop.specified_for.name!r} "
                f"in the XSD with the type: {type_anno}",
            )

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            # NOTE (mristin, 2022-05-26):
            # We need to check for the concrete descendants. If there are no concrete
            # descendants, there is no choice group either. Notably, this not only
            # applies to concrete classes, but there is no choice group for the abstract
            # classes without descendants either.
            if len(our_type.concrete_descendants) > 0:
                choice_group_name = xsd_naming.choice_group_name(our_type.name)
                xs_group = ET.Element(
                    "xs:group",
                    {
                        "ref": choice_group_name,
                        "minOccurs": min_occurs,
                        "maxOccurs": max_occurs,
                    },
                )

                xs_sequence = ET.Element("xs:sequence")
                xs_sequence.append(xs_group)

                xs_complex_type = ET.Element("xs:complexType")
                xs_complex_type.append(xs_sequence)

                xs_element = ET.Element(
                    "xs:element", {"name": naming.xml_property(prop.name)}
                )
                xs_element.append(xs_complex_type)
            else:
                xs_element_inner = ET.Element(
                    "xs:element",
                    {
                        "name": naming.xml_class_name(our_type.name),
                        "type": xsd_naming.type_name(our_type.name),
                        "minOccurs": min_occurs,
                        "maxOccurs": max_occurs,
                    },
                )
                xs_sequence = ET.Element("xs:sequence")
                xs_sequence.append(xs_element_inner)

                xs_complex_type = ET.Element("xs:complexType")
                xs_complex_type.append(xs_sequence)

                xs_element = ET.Element(
                    "xs:element", {"name": naming.xml_property(prop.name)}
                )
                xs_element.append(xs_complex_type)

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            return None, Error(
                prop.parsed.node,
                f"We do not know how to specify the list of constrained primitives "
                f"for the property {prop.name!r} of {prop.specified_for.name!r} "
                f"in the XSD with the type: {type_anno}",
            )
        else:
            assert_never(our_type)
    else:
        return None, Error(
            prop.parsed.node,
            f"We do not know how to specify the list "
            f"for the property {prop.name!r} of {prop.specified_for.name!r} "
            f"in the XSD with the type: {type_anno}",
        )

    return xs_element, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_xs_element_for_a_property(
    prop: intermediate.Property,
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
) -> Tuple[Optional[ET.Element], Optional[Error]]:
    """Generate the definition of an ``xs:element`` for a property."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    xs_element: Optional[ET.Element]

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        xs_element, error = _generate_xs_element_for_a_primitive_property(
            prop=prop,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints,
        )
        if error is not None:
            return None, error
        assert xs_element is not None

    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        our_type = type_anno.our_type

        if isinstance(our_type, intermediate.Enumeration):
            xs_element = ET.Element(
                "xs:element",
                {
                    "name": naming.xml_property(prop.name),
                    "type": xsd_naming.type_name(our_type.name),
                },
            )

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            xs_element, error = _generate_xs_element_for_a_primitive_property(
                prop=prop,
                len_constraint=len_constraint,
                pattern_constraints=pattern_constraints,
            )
            if error is not None:
                return None, error
            assert xs_element is not None

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            # NOTE (mristin, 2022-05-26):
            # We generate choices only if there are at least one concrete descendant.
            # Otherwise, the choice is not generated. Hence, we need to reference
            # a choice only if there is actually one.
            #
            # This is especially necessary for abstract classes with no descendants
            # which we still want to include in the schema. We simply generate an empty
            # element in the schema for such abstract classes without descendants.
            if len(our_type.concrete_descendants) > 0:
                xs_sequence = ET.Element("xs:sequence")
                xs_sequence.append(
                    ET.Element(
                        "xs:group", {"ref": xsd_naming.choice_group_name(our_type.name)}
                    )
                )

                xs_complex_type = ET.Element("xs:complexType")
                xs_complex_type.append(xs_sequence)

                xs_element = ET.Element(
                    "xs:element", {"name": naming.xml_property(prop.name)}
                )
                xs_element.append(xs_complex_type)
            else:
                xs_element = ET.Element(
                    "xs:element",
                    {
                        "name": naming.xml_property(prop.name),
                        "type": xsd_naming.type_name(our_type.name),
                    },
                )
        else:
            assert_never(type_anno.our_type)

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        xs_element, error = _generate_xs_element_for_a_list_property(
            prop=prop, len_constraint=len_constraint
        )
        if error is not None:
            return None, error

        assert xs_element is not None
    else:
        assert_never(type_anno)

    assert xs_element is not None

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        xs_element.attrib["minOccurs"] = "0"
        xs_element.attrib["maxOccurs"] = "1"

    return xs_element, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_properties(
    cls: intermediate.ClassUnion,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[List[ET.Element]], Optional[List[Error]]]:
    """Define the properties of the ``cls`` as a sequence of tags."""
    sequence = []  # type: List[ET.Element]
    errors = []  # type: List[Error]

    for prop in cls.properties:
        if prop.specified_for is not cls:
            continue

        len_constraint = constraints_by_property.len_constraints_by_property.get(
            prop, None
        )

        pattern_constraints = constraints_by_property.patterns_by_property.get(
            prop, None
        )

        xs_element, error = _generate_xs_element_for_a_property(
            prop=prop,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints,
        )
        if error is not None:
            errors.append(error)
        else:
            assert xs_element is not None
            sequence.append(xs_element)

    if len(errors) > 0:
        return None, errors

    return sequence, None


def _generate_xs_group_for_class(
    cls: intermediate.ClassUnion,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[ET.Element], Optional[Error]]:
    """Generate the ``xs:group`` representation of the class properties."""
    properties, properties_errors = _define_properties(
        cls=cls, constraints_by_property=constraints_by_property
    )

    if properties_errors is not None:
        return None, Error(
            cls.parsed.node,
            f"Failed to generate xs:group for the class {cls.name!r}",
            properties_errors,
        )

    assert properties is not None

    xs_sequence = ET.Element("xs:sequence")
    for inheritance in cls.inheritances:
        inheritance_xs_group = ET.Element(
            "xs:group", {"ref": xsd_naming.group_name(inheritance.name)}
        )
        xs_sequence.append(inheritance_xs_group)

    xs_sequence.extend(properties)

    xs_group = ET.Element("xs:group", {"name": xsd_naming.group_name(cls.name)})
    xs_group.append(xs_sequence)

    return xs_group, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_for_class(
    cls: intermediate.ClassUnion,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[List[ET.Element]], Optional[Error]]:
    """
    Generate the definitions for the class ``cls``.

    The root element is to be *extended* with the resulting list.
    """
    # NOTE (mristin, 2022-03-30):
    # We define each set of properties in a group. Then we reference these groups
    # among the complex types.
    # See: https://stackoverflow.com/questions/1198755/xml-schemas-with-multiple-inheritance

    xs_group, xs_group_error = _generate_xs_group_for_class(
        cls=cls, constraints_by_property=constraints_by_property
    )
    if xs_group_error is not None:
        return None, xs_group_error

    assert xs_group is not None

    xs_group_ref = ET.Element("xs:group", {"ref": xsd_naming.group_name(cls.name)})

    xs_sequence = ET.Element("xs:sequence")
    xs_sequence.append(xs_group_ref)

    complex_type = ET.Element(
        "xs:complexType", {"name": xsd_naming.type_name(cls.name)}
    )
    complex_type.append(xs_sequence)

    return [xs_group, complex_type], None


@require(lambda cls: len(cls.concrete_descendants) > 0)
def _generate_choice_group(cls: intermediate.ClassUnion) -> ET.Element:
    """Generate a group that defines a choice of concrete descendants."""
    xs_choice = ET.Element("xs:choice")

    if isinstance(cls, intermediate.ConcreteClass):
        xs_choice.append(
            ET.Element(
                "xs:element",
                {
                    "name": naming.xml_class_name(cls.name),
                    "type": xsd_naming.type_name(cls.name),
                },
            )
        )

    for descendant in cls.concrete_descendants:
        xs_choice.append(
            ET.Element(
                "xs:element",
                {
                    "name": naming.xml_class_name(descendant.name),
                    "type": xsd_naming.type_name(descendant.name),
                },
            )
        )

    xs_group = ET.Element("xs:group", {"name": xsd_naming.choice_group_name(cls.name)})
    xs_group.append(xs_choice)
    return xs_group


_WHITESPACE_RE = re.compile(r"\s+")


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _retrieve_implementation_specific_elements(
    cls: intermediate.ClassUnion,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[List[ET.Element]], Optional[List[Error]]]:
    """Parse the elements from the implementation-specific snippet."""
    implementation_key = specific_implementations.ImplementationKey(f"{cls.name}.xml")

    text = spec_impls.get(implementation_key, None)
    if text is None:
        return None, [
            Error(
                cls.parsed.node,
                f"The implementation is missing "
                f"for the implementation-specific class: {implementation_key}",
            )
        ]

    implementation_root: ET.Element

    try:
        implementation_root = ET.fromstring(text)
    except Exception as err:
        return None, [
            Error(
                cls.parsed.node,
                f"Failed to parse the XML out of "
                f"the specific implementation {implementation_key}: {err}",
            )
        ]

    errors = []  # type: List[Error]
    for descendant in implementation_root.iter():
        if descendant.text is not None and not _WHITESPACE_RE.fullmatch(
            descendant.text
        ):
            errors.append(
                Error(
                    cls.parsed.node,
                    f"Unexpected text "
                    f"in the specific implementation {implementation_key} "
                    f"in an element with tag {descendant.tag!r}: {descendant.text!r}",
                )
            )
            continue

        if descendant.tail is not None and not _WHITESPACE_RE.fullmatch(
            descendant.tail
        ):
            errors.append(
                Error(
                    cls.parsed.node,
                    f"Unexpected tail text "
                    f"in the specific implementation {implementation_key} "
                    f"in an element with tag {descendant.tag!r}: {descendant.tail!r}",
                )
            )
            continue

    if len(errors) > 0:
        return None, errors

    # Ignore the implementation root since it defines a partial schema
    elements = []  # type: List[ET.Element]
    for child in implementation_root:
        elements.append(child)

    return elements, None


def _sort_by_tags_and_names_in_place(root: ET.Element) -> None:
    """
    Sort the children elements by tag and name attribute in place.

    This makes diffing and searching in the schema a bit easier.
    """
    groups = []  # type: List[ET.Element]
    simple_types = []  # type: List[ET.Element]
    complex_types = []  # type: List[ET.Element]
    miscellaneous = []  # type: List[ET.Element]
    elements = []  # type: List[ET.Element]

    for child in root:
        if child.tag == "xs:group":
            groups.append(child)
        elif child.tag == "xs:simpleType":
            simple_types.append(child)
        elif child.tag == "xs:complexType":
            complex_types.append(child)
        elif child.tag == "xs:element":
            elements.append(child)
        else:
            miscellaneous.append(child)

    for element_list in [groups, simple_types, complex_types, miscellaneous, elements]:
        element_list.sort(key=lambda elt: elt.attrib.get("name", ""))

    children = groups + simple_types + complex_types + elements + miscellaneous

    assert len(children) == len(root)
    root[:] = children


_EXPLANATION_ABOUT_WHY_WE_EXPECT_VALUE_DATA_TYPE = (
    "(mristin, 2022-09-02) "
    'We provide an internal data type ``valueDataType`` to correspond to "any XSD '
    'atomic type as specified via DataTypeDefXsd". We need this type since we '
    "hard-wire ``Value_data_type`` to it. We could have made "
    "the class ``Value_data_type``implementation-specific and defined its "
    "representation manually as a snippet, including ``valueDataType``.\n\n"
    "However, we decided against that. This would be a major hurdle for "
    "other code and test data generators (which can treat ``Value_data_type`` "
    "simply as string). Therefore, we make the XSD generator "
    "a bit more hacky instead of complicating the other generators.\n\n"
    "If in the future, for whatever reason, the semantic of ``Value_data_type`` "
    "changes (or the type is renamed), be careful to maintain backwards "
    "compatibility here! You probably want to distinguish different versions "
    "of the meta-model and act accordingly. At that point, it might also make "
    "sense to refactor this schema generator to a separate repository, and "
    "fix it to a particular range of meta-model versions."
)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the XML Schema Definition (XSD) based on the ``symbol_table."""
    root_element_key = specific_implementations.ImplementationKey("root_element.xml")

    root_element_as_text = spec_impls.get(root_element_key, None)
    if root_element_as_text is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the root element "
                f"is missing: {root_element_key}",
            )
        ]

    root: ET.Element
    try:
        root = ET.fromstring(root_element_as_text)
    except ET.ParseError as err:
        return None, [
            Error(
                None, f"Failed to parse the root element from {root_element_key}: {err}"
            )
        ]

    # NOTE (mristin, 2022-03-30):
    # We need to use minidom to extract the ``xmlns`` property as ElementTree removes
    # it.
    # noinspection PyUnresolvedReferences
    minidom_doc = xml.dom.minidom.parseString(root_element_as_text)

    if not minidom_doc.documentElement.hasAttribute("xmlns"):
        return None, [
            Error(
                None,
                f"The implementation snippet for the root element "
                f"is missing the 'xmlns' attribute: {root_element_key}",
            )
        ]

    xmlns = minidom_doc.documentElement.getAttribute("xmlns")

    if xmlns != symbol_table.meta_model.xml_namespace:
        return None, [
            Error(
                None,
                f"The 'xmlns' attribute of the implementation snippet "
                f"{root_element_key} for the root element "
                f"and the '__xml_namespace__' of the meta-model "
                f"do not coincide: "
                f"{xmlns!r} != {symbol_table.meta_model.xml_namespace!r}",
            )
        ]

    if not minidom_doc.documentElement.hasAttribute("targetNamespace"):
        return None, [
            Error(
                None,
                f"The implementation snippet for the root element "
                f"is missing the 'targetNamespace' attribute: {root_element_key}",
            )
        ]

    target_namespace = minidom_doc.documentElement.getAttribute("targetNamespace")
    if target_namespace != symbol_table.meta_model.xml_namespace:
        return None, [
            Error(
                None,
                f"The 'targetNamespace' attribute of the implementation snippet "
                f"{root_element_key} for the root element "
                f"and the '__xml_namespace__' of the meta-model "
                f"do not coincide: "
                f"{target_namespace!r} != {symbol_table.meta_model.xml_namespace!r}",
            )
        ]

    assert root is not None

    errors = []  # type: List[Error]

    # NOTE (mristin, 2022-04-09):
    # We remove any whitespace tail and text in all the tags, and make sure there is no
    # unexpected text anywhere.
    for element in root.iter():
        if element.text is not None:
            if _WHITESPACE_RE.fullmatch(element.text):
                element.text = None
            else:
                errors.append(
                    Error(
                        None,
                        f"Unexpected text in an element with tag {element.tag!r} "
                        f"from the snippet {root_element_key!r}: {element.text!r}",
                    )
                )

        if element.tail is not None:
            if _WHITESPACE_RE.fullmatch(element.tail):
                element.tail = None
            else:
                errors.append(
                    Error(
                        None,
                        f"Unexpected tail in an element with tag {element.tag!r} "
                        f"from the snippet {root_element_key!r}: {element.tail!r}",
                    )
                )

    if len(errors) > 0:
        return None, errors

    constraints_by_class, some_errors = infer_for_schema.infer_constraints_by_class(
        symbol_table=symbol_table
    )

    if some_errors is not None:
        errors.extend(some_errors)

    # NOTE (mristin, 2022-11-10):
    # Please see :py:const:`_EXPLANATION_ABOUT_WHY_WE_EXPECT_VALUE_DATA_TYPE` for
    # the explanation why we retrieve the ``Value_data_type`` here
    value_data_type_cls = symbol_table.find_our_type(Identifier("Value_data_type"))

    if value_data_type_cls is None:
        errors.append(
            Error(
                None,
                "XSD generator expected to find our type ``Value_data_type``, but it "
                "was not present in the meta-model.\n\n"
                + _EXPLANATION_ABOUT_WHY_WE_EXPECT_VALUE_DATA_TYPE,
            )
        )
    elif not isinstance(value_data_type_cls, intermediate.ConstrainedPrimitive):
        errors.append(
            Error(
                None,
                "XSD generator expected ``Value_data_type`` to be "
                "a constrained primitive,  but got: {type(value_data_type_cls)}.\n\n"
                + _EXPLANATION_ABOUT_WHY_WE_EXPECT_VALUE_DATA_TYPE,
            )
        )
    elif value_data_type_cls.constrainee != intermediate.PrimitiveType.STR:
        errors.append(
            Error(
                None,
                f"XSD generator expected ``Value_data_type`` to be a constrained "
                f"primitive of strings, "
                f"but got: {value_data_type_cls.constrainee}.\n\n"
                + _EXPLANATION_ABOUT_WHY_WE_EXPECT_VALUE_DATA_TYPE,
            )
        )
    else:
        # Our type ``Value_data_type`` is as expected.
        pass

    if len(errors) > 0:
        return None, errors

    assert constraints_by_class is not None

    ids_of_our_types_in_properties = (
        intermediate.collect_ids_of_our_types_in_properties(symbol_table=symbol_table)
    )

    # region Specify ``valueDataType``

    assert value_data_type_cls is not None

    value_data_type_element = ET.Element(
        "xs:simpleType", attrib={"name": "valueDataType"}
    )

    value_data_type_element.append(
        ET.Element(
            "xs:restriction",
            attrib={"base": "xs:string"},
        )
    )

    root.append(value_data_type_element)

    # endregion

    for our_type in symbol_table.our_types:
        if our_type.name == "Value_data_type":
            # NOTE (mristin, 2022-11-10):
            # Please see :py:const:`_EXPLANATION_ABOUT_WHY_WE_EXPECT_VALUE_DATA_TYPE`
            # for the explanation why we hard-wire the ``Value_data_type`` here
            continue

        elements: Optional[List[ET.Element]]

        if (
            isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            )
            and our_type.is_implementation_specific
        ):
            elements, impl_spec_errors = _retrieve_implementation_specific_elements(
                cls=our_type, spec_impls=spec_impls
            )
            if impl_spec_errors is not None:
                errors.extend(impl_spec_errors)
                continue

            assert elements is not None
        else:
            if isinstance(our_type, intermediate.Enumeration):
                if id(our_type) not in ids_of_our_types_in_properties:
                    continue

                elements = _define_for_enumeration(enumeration=our_type)

            elif isinstance(our_type, intermediate.ConstrainedPrimitive):
                # NOTE (mristin, 2022-03-30):
                # We in-line the constraints from the constrained primitives directly
                # in the properties. We do not want to introduce separate definitions
                # for them as that would make it more difficult for downstream code
                # generators to generate meaningful code.

                continue

            elif isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                elements, definition_error = _define_for_class(
                    cls=our_type, constraints_by_property=constraints_by_class[our_type]
                )

                if definition_error is not None:
                    errors.append(definition_error)
                    continue

                assert elements is not None

                if len(our_type.concrete_descendants) > 0:
                    choice_group = _generate_choice_group(cls=our_type)
                    elements.append(choice_group)
            else:
                assert_never(our_type)

        assert elements is not None
        root.extend(elements)

    if len(errors) > 0:
        return None, errors

    # Tag name 🠒 (name 🠒 element)
    observed_definitions = dict(
        dict()
    )  # type: MutableMapping[str, MutableMapping[str, ET.Element]]

    for element in root:
        name = element.attrib.get("name", None)
        if name is None:
            continue

        observed_for_tag = observed_definitions.get(element.tag, None)
        if observed_for_tag is None:
            observed_for_tag = dict()
            observed_definitions[element.tag] = observed_for_tag

        observed_element = observed_for_tag.get(name, None)
        if observed_element is not None:
            ours = ET.tostring(element, encoding="unicode", method="xml")
            theirs = ET.tostring(observed_element, encoding="unicode", method="xml")

            errors.append(
                Error(
                    None,
                    f"There are conflicting definitions in the schema "
                    f"with the name {name!r}:\n"
                    f"\n"
                    f"{ours}\n"
                    f"\n"
                    f"and\n"
                    f"\n"
                    f"{theirs}",
                )
            )
        else:
            observed_for_tag[name] = element

    if len(errors) > 0:
        return None, errors

    _sort_by_tags_and_names_in_place(root)

    # NOTE (mristin, 2022-03-30):
    # For some unknown reason, ElementTree erases the xmlns property of the root
    # element. Therefore, we need to add it here manually.
    root.attrib["xmlns"] = xmlns

    text = ET.tostring(root, encoding="unicode", method="xml")

    # NOTE (mristin, 2021-11-23):
    # This approach is slow, but effective. As long as the meta-model is not too big,
    # this should work.
    # noinspection PyUnresolvedReferences
    pretty_text = xml.dom.minidom.parseString(text).toprettyxml(indent="  ")

    return pretty_text, None


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    code, errors = _generate(
        symbol_table=context.symbol_table, spec_impls=context.spec_impls
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the XML Schema Definition "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "schema.xsd"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the XML Schema Definition to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
