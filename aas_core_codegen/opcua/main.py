"""Generate the OPC UA Schema node set corresponding to the meta-model."""
import collections
import dataclasses
import enum
import io
import itertools
import re
import xml.dom.minidom
import xml.etree.ElementTree as ET
import xml.sax.saxutils
from typing import (
    TextIO,
    Tuple,
    Optional,
    List,
    MutableMapping,
    Mapping,
    Union,
    OrderedDict,
    Iterable,
    Set,
)

from icontract import ensure, require

import aas_core_codegen.opcua
import aas_core_codegen.opcua.naming as opcua_naming
from aas_core_codegen import (
    run,
    intermediate,
    specific_implementations,
)
from aas_core_codegen.common import (
    Error,
    assert_never,
    Identifier,
    IDENTIFIER_RE,
    Stripped,
)

assert aas_core_codegen.opcua.__doc__ == __doc__

_PRIMITIVE_MAP = {
    intermediate.PrimitiveType.BOOL: "Boolean",
    intermediate.PrimitiveType.INT: "Int64",
    intermediate.PrimitiveType.FLOAT: "Double",
    intermediate.PrimitiveType.STR: "String",
    intermediate.PrimitiveType.BYTEARRAY: "ByteString",
}
assert all(literal in _PRIMITIVE_MAP for literal in intermediate.PrimitiveType)


class _IdentifierMachine:
    """
    Produce stable identifiers for different nodes.

    The Identifier Machine knows nothing about your scheme, so you have to come up
    with your own.

    It will try to be as stable as possible, *i.e.*, the identifiers for the names
    should not change even if the order of :py:func:`obtain` is changed.

    >>> machine = _IdentifierMachine()
    >>> machine.obtain("something")
    207137056

    Obtaining an identifier is idem-potent:

    >>> machine.obtain("something")
    207137056

    Another text gives you another identifier:

    >>> machine.obtain("something_else")
    165180381
    """

    def __init__(self) -> None:
        self._identifier_map = dict()  # type: MutableMapping[str, int]
        self._taken_identifiers = set()  # type: Set[int]

    @staticmethod
    def _hash(text: str) -> int:
        """
        Compute the non-cryptographic hash of the given string.

        We implement our own hash so that the implementation need not change across
        different Python versions, in case they change the hash function.

        >>> _IdentifierMachine._hash("something")
        207137056

        >>> _IdentifierMachine._hash("something_else")
        165180381

        >>> _IdentifierMachine._hash("")
        7
        """
        result = 7
        for character in text:
            result = (result * 31 + ord(character)) % 0x7FFFFFFF

        return result

    def obtain(self, text: str) -> int:
        """
        Assign a slot for the text using hashing.

        In most cases, we do not expect the resulting ID to change.
        """
        identifier = self._identifier_map.get(text, None)
        if identifier is not None:
            return identifier

        identifier = _IdentifierMachine._hash(text)

        while identifier in self._taken_identifiers:
            identifier += 1

        self._taken_identifiers.add(identifier)
        self._identifier_map[text] = identifier

        return identifier


def _generate_aliases() -> ET.Element:
    """Generate the aliases including the primitive values."""
    aliases = ET.Element("Aliases")

    for name, i in (
        ("Boolean", 1),
        ("Int64", 8),
        ("Double", 11),
        ("String", 12),
        ("ByteString", 15),
        ("HasModellingRule", 37),
        ("HasTypeDefinition", 40),
        ("HasSubtype", 45),
        ("HasProperty", 46),
        ("HasComponent", 47),
        ("HasInterface", 17603),
    ):
        alias = ET.Element("Alias", {"Alias": name})
        alias.text = f"i={i}"
        aliases.append(alias)

    return aliases


@dataclasses.dataclass
class _IdentifiersForConstraints:
    """Map the references and object types for constraints to identifiers."""

    constraint_id: int
    constraint_identifier_id: int
    constraint_text_id: int
    has_constraint_id: int


def _generate_for_constraints_and_patterns(
    identifiers_for_constraints: _IdentifiersForConstraints,
) -> List[ET.Element]:
    """Generate the object types and the references to represent constraints."""
    return [
        ET.fromstring(
            f"""\
<UAObjectType
        NodeId="ns=1;i={identifiers_for_constraints.constraint_id}"
        BrowseName="1:Constraint"
>
    <DisplayName>Constraint</DisplayName>
    <References>
        <Reference ReferenceType="HasSubtype" IsForward="false">i=58</Reference>
        <Reference
            ReferenceType="HasProperty"
        >ns=1;i={identifiers_for_constraints.constraint_identifier_id}</Reference>
        <Reference
            ReferenceType="HasProperty"
        >ns=1;i={identifiers_for_constraints.constraint_text_id}</Reference>
    </References>
</UAObjectType>"""
        ),
        ET.fromstring(
            f"""\
<UAVariable
        NodeId="ns=1;i={identifiers_for_constraints.constraint_identifier_id}"
        BrowseName="1:identifier"
        ParentNodeId="ns=1;i={identifiers_for_constraints.constraint_id}"
        DataType="String"
>
    <DisplayName>identifier</DisplayName>
    <References>
        <Reference ReferenceType="HasTypeDefinition">i=68</Reference>
        <Reference ReferenceType="HasModellingRule">i=80</Reference>
    </References>
</UAVariable>"""
        ),
        ET.fromstring(
            f"""\
<UAVariable
        NodeId="ns=1;i={identifiers_for_constraints.constraint_text_id}"
        BrowseName="1:text"
        ParentNodeId="ns=1;i={identifiers_for_constraints.constraint_id}"
        DataType="String"
>
    <DisplayName>text</DisplayName>
    <References>
        <Reference ReferenceType="HasTypeDefinition">i=68</Reference>
        <Reference ReferenceType="HasModellingRule">i=78</Reference>
    </References>
</UAVariable>"""
        ),
        ET.fromstring(
            f"""\
<UAReferenceType
        NodeId="ns=1;i={identifiers_for_constraints.has_constraint_id}"
        BrowseName="1:HasConstraint"
>
    <DisplayName>HasConstraint</DisplayName>
    <References>
        <Reference ReferenceType="HasSubtype" IsForward="false">i=32</Reference>
    </References>
    <InverseName>Constrains</InverseName>
</UAReferenceType>"""
        ),
    ]


#: All the classes whose instances have an ``i=...`` in the node set.
_OpcUaIdentifiable = Union[
    intermediate.Enumeration,
    intermediate.ConstrainedPrimitive,
    intermediate.Class,
    intermediate.Interface,
    intermediate.Property,
    intermediate.Invariant,
]


def _reference(
    reference_type: str, target: str, is_forward: Optional[bool] = None
) -> ET.Element:
    """Create a ``<Reference>`` element."""
    attrib = collections.OrderedDict([("ReferenceType", reference_type)])
    if is_forward is not None:
        attrib["IsForward"] = "true" if is_forward else "false"

    reference_el = ET.Element("Reference", attrib)
    reference_el.text = target

    return reference_el


def _localized_text(text: str) -> ET.Element:
    """Create a nested ``<uax:LocalizedText>``."""
    localized_text_el = ET.Element("uax:LocalizedText")

    text_el = ET.Element("uax:Text")
    localized_text_el.append(text_el)

    text_el.text = text

    return localized_text_el


def _generate_for_enum(
    enumeration: intermediate.Enumeration,
    identifier_map: Mapping[_OpcUaIdentifiable, int],
    identifier_machine: _IdentifierMachine,
    name_prefix: Identifier,
) -> List[ET.Element]:
    """Define the enumeration as OPC UA EnumStrings."""
    enum_name = opcua_naming.enum_name(enumeration.name, name_prefix)

    result = []  # type: List[ET.Element]

    comment_starts = ET.Comment(f"{enum_name} starts.")
    comment_starts.tail = "\n"
    result.append(comment_starts)

    enum_id = identifier_map[enumeration]

    def generate_data_type() -> ET.Element:
        """Generate the element defining the data type."""
        data_type_el = ET.Element(
            "UADataType",
            collections.OrderedDict(
                [("NodeId", f"ns=1;i={enum_id}"), ("BrowseName", f"1:{enum_name}")]
            ),
        )

        display_name_el = ET.Element("DisplayName")
        data_type_el.append(display_name_el)
        display_name_el.text = enum_name

        references_el = ET.Element("References")
        data_type_el.append(references_el)
        references_el.append(
            _reference(reference_type="HasSubtype", target="i=29", is_forward=False)
        )

        definition_el = ET.Element("Definition", {"Name": f"1:{enum_name}"})
        data_type_el.append(definition_el)

        for i, literal in enumerate(enumeration.literals):
            field = ET.Element(
                "Field",
                collections.OrderedDict(
                    [
                        ("Name", opcua_naming.enum_literal_name(literal.name)),
                        ("Value", str(i)),
                    ]
                ),
            )
            definition_el.append(field)

        return data_type_el

    result.append(generate_data_type())

    def generate_enum_strings() -> ET.Element:
        """Generate the EnumString for the enumeration."""
        variable_id = identifier_machine.obtain(f"{enumeration.name}:variable")

        variable_el = ET.Element(
            "UAVariable",
            collections.OrderedDict(
                [
                    ("DataType", "LocalizedText"),
                    ("ValueRank", "1"),
                    ("NodeId", f"ns=1;i={variable_id}"),
                    ("ArrayDimensions", str(len(enumeration.literals))),
                    ("BrowseName", "EnumStrings"),
                    ("ParentNodeId", f"ns=1;i={enum_id}"),
                ]
            ),
        )

        display_name_el = ET.Element("DisplayName")
        variable_el.append(display_name_el)
        display_name_el.text = "EnumStrings"

        references_el = ET.Element("References")
        variable_el.append(references_el)
        references_el.append(
            _reference("HasProperty", target=f"ns=1;i={enum_id}", is_forward=False)
        )
        references_el.append(_reference("HasTypeDefinition", target="i=68"))
        references_el.append(_reference("HasModellingRule", target="i=78"))

        value_el = ET.Element("Value")
        variable_el.append(value_el)

        list_of_localized_text_el = ET.Element("uax:ListOfLocalizedText")
        value_el.append(list_of_localized_text_el)

        for literal in enumeration.literals:
            list_of_localized_text_el.append(_localized_text(literal.value))

        return variable_el

    result.append(generate_enum_strings())

    comment_ends = ET.Comment(f"{enum_name} ends.")
    comment_ends.tail = "\n"
    result.append(comment_ends)

    return result


_CONSTRAINT_ID_PREFIX_RE = re.compile(r"Constraint \s*(?P<identifier>[^:]+)\s*:")


def _extract_constraint_identifier(description: str) -> Optional[str]:
    """
    Try to extract the constraint identifier from the invariant description.

    >>> _extract_constraint_identifier("Constraint 1: bla bla bla")
    '1'

    >>> _extract_constraint_identifier("Constraint  1 : bla bla bla")
    '1'

    >>> _extract_constraint_identifier("Bla bla bla")

    >>> _extract_constraint_identifier("Constraint 2: Name with at most 9 characters.")
    '2'
    """
    match = _CONSTRAINT_ID_PREFIX_RE.match(description)

    if match is None:
        return None

    return match.group("identifier").strip()


def _value_string(text: str) -> ET.Element:
    """Generate an ``<Value>`` element with the embedded string element."""
    value_el = ET.Element("Value")

    uax_string_el = ET.Element("uax:String")
    value_el.append(uax_string_el)
    uax_string_el.text = text

    return value_el


def _generate_for_invariant(
    invariant: intermediate.Invariant,
    identifier_map: Mapping[_OpcUaIdentifiable, int],
    identifiers_for_constraints: _IdentifiersForConstraints,
    identifier_machine: _IdentifierMachine,
) -> List[ET.Element]:
    """Generate the constraint object for the invariant."""
    assert (
        invariant in identifier_map
    ), f"Invariant {invariant.description!r} missing in identifier map"

    invariant_id = identifier_map[invariant]

    constraint_identifier = _extract_constraint_identifier(invariant.description)

    if constraint_identifier is None:
        browse_name = f"ConstraintUnlabeled{invariant_id}"
    else:
        browse_name = opcua_naming.constraint_browser_name(
            Stripped(constraint_identifier)
        )

    object_el = ET.fromstring(
        f"""\
<UAObject
        NodeId="ns=1;i={invariant_id}"
        BrowseName="1:{browse_name}"
        ParentNodeId="i=85"
>
    <DisplayName>{browse_name}</DisplayName>
    <References>
        <Reference ReferenceType="Organizes" IsForward="false">i=85</Reference>
        <Reference
                ReferenceType="HasTypeDefinition"
        >ns=1;i={identifiers_for_constraints.constraint_id}</Reference>
    </References>
</UAObject>"""
    )

    text_id = identifier_machine.obtain(f"{invariant_id}:text")

    text_variable_el = ET.fromstring(
        f"""\
<UAVariable
        DataType="String"
        NodeId="ns=1;i={text_id}"
        BrowseName="1:text"
        ParentNodeId="ns=1;i={invariant_id}"
>
    <DisplayName>text</DisplayName>
    <References>
        <Reference
                ReferenceType="HasProperty"
                IsForward="false"
        >ns=1;i={invariant_id}</Reference>
        <Reference ReferenceType="HasTypeDefinition">i=63</Reference>
    </References>
</UAVariable>"""
    )

    # NOTE (mristin):
    # We have to create the ``<Value>`` ourselves as we use a namespace alias and
    # the ElementTree can not parse the namespace aliases from string.
    text_variable_el.append(_value_string(invariant.description))

    result = [object_el, text_variable_el]

    if constraint_identifier is not None:
        identifier_id = identifier_machine.obtain(f"{invariant_id}:identifier")
        identifier_variable_el = ET.fromstring(
            f"""\
<UAVariable
        DataType="String"
        NodeId="ns=1;i={identifier_id}"
        BrowseName="1:identifier"
        ParentNodeId="ns=1;i={invariant_id}"
>
    <DisplayName>identifier</DisplayName>
    <References>
        <Reference
                ReferenceType="HasProperty"
                IsForward="false"
        >ns=1;i={invariant_id}</Reference>
        <Reference ReferenceType="HasTypeDefinition">i=63</Reference>
    </References>
</UAVariable>"""
        )

        # NOTE (mristin):
        # We have to create the ``<Value>`` ourselves as we use a namespace alias and
        # the ElementTree can not parse the namespace aliases from string.
        identifier_variable_el.append(_value_string(constraint_identifier))

        result.append(identifier_variable_el)

    return result


def _generate_for_constrained_primitive(
    constrained_primitive: intermediate.ConstrainedPrimitive,
    identifier_map: Mapping[_OpcUaIdentifiable, int],
    identifiers_for_constraints: _IdentifiersForConstraints,
    name_prefix: Identifier,
) -> ET.Element:
    """Define the constrained primitive and link it with constraints."""
    constrained_primitive_name = opcua_naming.constrained_primitive_name(
        constrained_primitive.name, prefix=name_prefix
    )
    constrained_primitive_id = identifier_map[constrained_primitive]

    root = ET.fromstring(
        f"""\
<UADataType
        NodeId="ns=1;i={constrained_primitive_id}"
        BrowseName="1:{constrained_primitive_name}"
>
    <DisplayName>{constrained_primitive_name}</DisplayName>
    <References>
        <Reference
                ReferenceType="HasSubtype"
                IsForward="false"
        >{_PRIMITIVE_MAP[constrained_primitive.constrainee]}</Reference>
    </References>
</UADataType>"""
    )

    references_el = root.find("References")
    assert references_el is not None, "Expected <References> in the node"

    for invariant in constrained_primitive.invariants:
        # NOTE (mristin):
        # We do not model inheritance between the constrained primitives as this
        # is not possible in OPC UA. Hence, we define all the constraints for each
        # constrained primitive. This causes a lot of repetition, but we found no other
        # way around it.

        invariant_id = identifier_map[invariant]

        references_el.append(
            ET.fromstring(
                f"""\
<Reference
        ReferenceType="ns=1;i={identifiers_for_constraints.has_constraint_id}"
>ns=1;i={invariant_id}</Reference>"""
            )
        )

    return root


class _PropertyReferenceType(enum.Enum):
    PROPERTY = 0
    COMPONENT = 1


def _determine_property_reference_type(
    prop: intermediate.Property,
) -> _PropertyReferenceType:
    """
    Determine how to map the given property.

    In OPC UA, we distinguish between properties — attributes with simple data types or
    arrays of simple data types — and components — references to instances
    or aggregations of instances.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if (intermediate.try_primitive_type(type_anno) is not None) or (
        isinstance(type_anno, intermediate.ListTypeAnnotation)
        and intermediate.try_primitive_type(type_anno.items) is not None
    ):
        return _PropertyReferenceType.PROPERTY

    return _PropertyReferenceType.COMPONENT


def _try_primitive_type(
    type_annotation: intermediate.TypeAnnotationUnion,
) -> Optional[intermediate.PrimitiveType]:
    """
    Inspect the type annotation and determine the underlying primitive type, if any.

    The primitive type can either be in the annotation itself, beneath an optional
    or beneath a list.

    This is different to :py:func:`intermediate.try_primitive_typ` since this function
    considers lists as well. This is because OPC UA does not distinguish between
    scalars and arrays when it comes to primitive types.
    """
    type_anno = intermediate.beneath_optional(type_annotation)

    # NOTE (mristin):
    # We make sure that we do not use the variable unintentionally.
    del type_annotation

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        return type_anno.a_type

    elif isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
        type_anno.our_type, intermediate.ConstrainedPrimitive
    ):
        return type_anno.our_type.constrainee

    elif isinstance(type_anno, intermediate.ListTypeAnnotation) and isinstance(
        type_anno.items, intermediate.PrimitiveTypeAnnotation
    ):
        return type_anno.items.a_type

    else:
        return None


def _generate_references_for_properties(
    properties: Iterable[intermediate.Property],
    identifier_map: Mapping[_OpcUaIdentifiable, int],
) -> List[ET.Element]:
    """
    Generate the ``<Reference>`` entries for the given properties.

    ``prop_to_id`` maps each property to an OPC UA identifier.
    """
    result = []  # type: List[ET.Element]

    for prop in properties:
        prop_id = identifier_map[prop]

        property_reference_type = _determine_property_reference_type(prop)
        if property_reference_type is _PropertyReferenceType.PROPERTY:
            result.append(_reference("HasProperty", f"ns=1;i={prop_id}"))
        elif property_reference_type is _PropertyReferenceType.COMPONENT:
            result.append(_reference("HasComponent", f"ns=1;i={prop_id}"))
        else:
            assert_never(property_reference_type)

    return result


@ensure(lambda result: result.tag in ("UAVariable", "UAObject"))
def _generate_for_property(
    prop: intermediate.Property,
    prop_id: int,
    parent_id: int,
    identifier_map: Mapping[_OpcUaIdentifiable, int],
) -> ET.Element:
    """Generate the variable element corresponding to the property."""
    prop_name = opcua_naming.property_name(prop.name)

    root = ET.Element(
        "",
        attrib=collections.OrderedDict(
            [
                ("NodeId", f"ns=1;i={prop_id}"),
                ("BrowseName", f"1:{prop_name}"),
                ("ParentNodeId", f"ns=1;i={parent_id}"),
            ]
        ),
    )

    display_name_el = ET.Element("DisplayName")
    root.append(display_name_el)
    display_name_el.text = prop_name

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        type_anno = prop.type_annotation.value
    else:
        type_anno = prop.type_annotation

    if isinstance(type_anno, intermediate.OptionalTypeAnnotation):
        raise AssertionError(
            "NOTE (mristin): We do not handle optional optionals, but you "
            f"specified type annotation {prop.type_annotation} for the property "
            f"{prop.name!r}."
        )

    if isinstance(type_anno, intermediate.ListTypeAnnotation):
        type_anno = type_anno.items

    elif isinstance(
        type_anno,
        (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
    ):
        pass

    else:
        assert_never(prop.type_annotation)
        raise AssertionError("Unexpected execution path")

    if not isinstance(
        type_anno,
        (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
    ):
        raise AssertionError(
            f"NOTE (mristin): We only implemented optional and mandatory lists of "
            f"primitives and lists of model instances, but you have "
            f"a property {prop.name} with type: {prop.type_annotation}. "
            f"Please contact the developers if you need this feature."
        )

    primitive_type = _try_primitive_type(type_anno)

    is_list = isinstance(
        intermediate.beneath_optional(prop.type_annotation),
        intermediate.ListTypeAnnotation,
    )
    is_optional = isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)

    references_el = ET.Element("References")
    if primitive_type is not None:
        if is_optional:
            # NOTE (mristin):
            # This corresponds to ``Optional``.
            references_el.append(_reference("HasModellingRule", target="i=80"))
        else:
            # NOTE (mristin):
            # This corresponds to ``Mandatory``.
            references_el.append(_reference("HasModellingRule", target="i=78"))
    else:
        if is_list:
            if is_optional:
                # NOTE (mristin):
                # This corresponds to ``OptionalPlaceholder``.
                references_el.append(_reference("HasModellingRule", target="i=11508"))
            else:
                # NOTE (mristin):
                # This corresponds to ``MandatoryPlaceholder``.
                references_el.append(_reference("HasModellingRule", target="i=11510"))
        else:
            if is_optional:
                # NOTE (mristin):
                # This corresponds to ``Optional``.
                references_el.append(_reference("HasModellingRule", target="i=80"))
            else:
                # NOTE (mristin):
                # This corresponds to ``Mandatory``.
                references_el.append(_reference("HasModellingRule", target="i=78"))

    if primitive_type is not None:
        if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
            root.attrib["DataType"] = _PRIMITIVE_MAP[primitive_type]

        elif isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
            type_anno.our_type, intermediate.ConstrainedPrimitive
        ):
            root.attrib["DataType"] = f"ns=1;i={identifier_map[type_anno.our_type]}"

        else:
            raise AssertionError(
                f"Unexpected primitive type in the property {prop.name!r} with "
                f"type annotation {prop.type_annotation} where the type annotation "
                f"beneath any Optional or List was: {type_anno}"
            )

        references_el.append(_reference("HasTypeDefinition", target="i=68"))

        if is_list:
            root.attrib["ValueRank"] = "1"

        root.tag = "UAVariable"
    else:
        if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
            raise AssertionError(
                "The case of the primitive type should have been handled before."
            )
        elif isinstance(type_anno, intermediate.OurTypeAnnotation):
            if isinstance(type_anno.our_type, intermediate.Enumeration):
                root.tag = "UAVariable"

                enum_id = identifier_map[type_anno.our_type]

                root.attrib["DataType"] = f"ns=1;i={enum_id}"

                references_el.append(_reference("HasTypeDefinition", target="i=62"))

            elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
                raise AssertionError(
                    "The case of the primitive type should have been handled before."
                )

            elif isinstance(
                type_anno.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            ):
                root.tag = "UAObject"

                if type_anno.our_type.interface is not None:
                    # NOTE (mristin):
                    # We specify the type as ``BaseObjectType`` since multiple
                    # inheritance is not possible.
                    references_el.append(_reference("HasTypeDefinition", target="i=58"))

                    interface_id = identifier_map[type_anno.our_type.interface]
                    references_el.append(
                        _reference("HasInterface", target=f"ns=1;i={interface_id}")
                    )

                    for ancestor_cls in type_anno.our_type.ancestors:
                        assert ancestor_cls.interface is not None

                        ancestor_id = identifier_map[ancestor_cls.interface]
                        references_el.append(
                            _reference("HasInterface", target=f"ns=1;i={ancestor_id}")
                        )

                    references_el.extend(
                        _generate_references_for_properties(
                            # NOTE (mristin):
                            # We reference *all* the properties of the object since
                            # the type definition is set to ``BaseObjectType``, but
                            # needs to satisfy all the interfaces.
                            properties=type_anno.our_type.properties,
                            identifier_map=identifier_map,
                        )
                    )

                else:
                    references_el.append(
                        _reference(
                            "HasTypeDefinition",
                            target=f"ns=1;i={identifier_map[type_anno.our_type]}",
                        )
                    )
            else:
                assert_never(type_anno.our_type)
        else:
            assert_never(type_anno)

    root.append(references_el)

    return root


def _generate_definitions_for_properties(
    parent_id: int,
    properties: Iterable[intermediate.Property],
    identifier_map: Mapping[_OpcUaIdentifiable, int],
) -> List[ET.Element]:
    """
    Generate the definition elements for all the properties.

    ``prop_to_id`` maps the properties to OPC UA identifiers.
    """
    result = []  # type: List[ET.Element]

    for prop in properties:
        prop_id = identifier_map[prop]

        property_el = _generate_for_property(
            prop=prop,
            prop_id=prop_id,
            parent_id=parent_id,
            identifier_map=identifier_map,
        )

        result.append(property_el)

    return result


def _generate_for_interface(
    interface: intermediate.Interface,
    identifier_map: Mapping[_OpcUaIdentifiable, int],
    identifiers_for_constraints: _IdentifiersForConstraints,
    name_prefix: Identifier,
) -> List[ET.Element]:
    """Generate the definition for the given interface."""
    interface_name = opcua_naming.interface_name(interface.name, name_prefix)

    comment_starts = ET.Comment(f"{interface_name} starts.")
    comment_starts.tail = "\n"

    result = [comment_starts]  # type: List[ET.Element]

    interface_id = identifier_map[interface]

    object_type_el = ET.Element(
        "UAObjectType",
        collections.OrderedDict(
            [
                ("NodeId", f"ns=1;i={interface_id}"),
                ("BrowseName", f"1:{interface_name}"),
                ("IsAbstract", "true"),
            ]
        ),
    )
    result.append(object_type_el)

    display_name_el = ET.Element("DisplayName")
    display_name_el.text = interface_name
    object_type_el.append(display_name_el)

    strictly_interface_properties = [
        prop for prop in interface.properties if prop.specified_for is interface.base
    ]

    references_el = ET.Element("References")
    object_type_el.append(references_el)

    references_el.append(_reference("HasSubtype", target="i=17602", is_forward=False))

    for invariant in interface.base.invariants:
        if invariant.specified_for is not interface.base:
            continue

        invariant_id = identifier_map[invariant]

        references_el.append(
            _reference(
                reference_type=f"ns=1;i={identifiers_for_constraints.has_constraint_id}",
                target=f"ns=1;i={invariant_id}",
            )
        )

    references_el.extend(
        _generate_references_for_properties(
            properties=strictly_interface_properties, identifier_map=identifier_map
        )
    )

    result.extend(
        _generate_definitions_for_properties(
            parent_id=interface_id,
            properties=strictly_interface_properties,
            identifier_map=identifier_map,
        )
    )

    comment_ends = ET.Comment(f"{interface_name} ends.")
    comment_ends.tail = "\n"
    result.append(comment_ends)

    return result


def _generate_for_concrete_class(
    cls: intermediate.ConcreteClass,
    identifier_map: Mapping[_OpcUaIdentifiable, int],
    identifiers_for_constraints: _IdentifiersForConstraints,
    name_prefix: Identifier,
) -> List[ET.Element]:
    """Generate the definition for the given concrete class."""
    cls_name = opcua_naming.class_name(cls.name, name_prefix)
    cls_id = identifier_map[cls]

    result = [ET.Comment(f"{cls_name} starts.")]  # type: List[ET.Element]

    object_type_el = ET.Element(
        "UAObjectType",
        attrib=collections.OrderedDict(
            [("NodeId", f"ns=1;i={cls_id}"), ("BrowseName", f"1:{cls_name}")]
        ),
    )

    display_name_el = ET.Element("DisplayName")
    display_name_el.text = cls_name
    object_type_el.append(display_name_el)

    references_el = ET.Element("References")
    references_el.append(_reference("HasSubtype", target="i=58", is_forward=False))

    if cls.interface is not None:
        interface_id = identifier_map[cls.interface]
        references_el.append(_reference("HasInterface", f"ns=1;i={interface_id}"))

    for ancestor_cls in cls.ancestors:
        assert ancestor_cls.interface is not None

        assert ancestor_cls.interface in identifier_map, (
            f"The OPC UA identifier is missing for the interface corresponding to "
            f"the ancestor class {ancestor_cls.name!r} of the class {cls.name!r}"
        )

        ancestor_id = identifier_map[ancestor_cls.interface]
        references_el.append(_reference("HasInterface", f"ns=1;i={ancestor_id}"))

    if cls.interface is None:
        # NOTE (mristin):
        # We have to reference the constraints here since this concrete class has no
        # interface, so no constraints have been referenced thus far. That is, we define
        # the constraints in interfaces, but this class has none, so we have to
        # reference them in the ``ObjectType`` corresponding to the class.
        for invariant in cls.invariants:
            if invariant.specified_for is not cls:
                continue

            invariant_id = identifier_map[invariant]

            references_el.append(
                _reference(
                    reference_type=f"ns=1;i={identifiers_for_constraints.has_constraint_id}",
                    target=f"ns=1;i={invariant_id}",
                )
            )

    else:
        # NOTE (mristin):
        # We assume that the object type needs to implement all the constraints imposed
        # on its interfaces. Since we define an interface for any concrete class with
        # descendants, we do not have to reference the constraints here.
        pass

    strictly_cls_properties = [
        prop for prop in cls.properties if prop.specified_for is cls
    ]

    references_el.extend(
        _generate_references_for_properties(
            properties=strictly_cls_properties, identifier_map=identifier_map
        )
    )

    object_type_el.append(references_el)
    result.append(object_type_el)

    # NOTE (mristin):
    # We define the properties only if they have not been already defined
    # for an interface.
    # Otherwise, we refer to the properties of the interfaces through
    # ``HasComponent``/``HasProperty`` reference.
    if cls.interface is None:
        result.extend(
            _generate_definitions_for_properties(
                parent_id=cls_id,
                properties=strictly_cls_properties,
                identifier_map=identifier_map,
            )
        )

    result.append(ET.Comment(f"{cls_name} ends."))

    return result


class _NamespaceDeclarations:
    #: URL of the main namespace
    main: str

    #: URL to namespace alias
    url_to_alias: Mapping[str, str]

    #: Namespace alias to URL
    alias_to_url: OrderedDict[str, str]

    # fmt: off
    @require(
        lambda url_to_alias, alias_to_url:
        all(
            alias_to_url[alias] == url
            for url, alias in url_to_alias.items()
        )
    )
    @require(
        lambda url_to_alias, alias_to_url:
        all(
            url_to_alias[url] == alias
            for alias, url in alias_to_url.items()
        )
    )
    # fmt: on
    def __init__(
        self,
        main: str,
        url_to_alias: Mapping[str, str],
        alias_to_url: OrderedDict[str, str],
    ) -> None:
        """Initialize with the given values."""
        self.main = main
        self.url_to_alias = url_to_alias
        self.alias_to_url = alias_to_url


def _extractNamespaceDeclarationsFromXML(
    text: str,
) -> Tuple[Optional[_NamespaceDeclarations], Optional[str]]:
    """
    Extract the namespace declarations from the given XML document.

    Return the parsed declarations, or error, if any.
    """
    minidom_doc = xml.dom.minidom.parseString(text)

    main = None  # type: Optional[str]
    url_to_alias = dict()  # type: MutableMapping[str, str]
    alias_to_url = collections.OrderedDict()  # type: OrderedDict[str, str]

    for attribute, value in minidom_doc.documentElement.attributes.items():
        if attribute == "xmlns":
            main = value
        elif attribute.startswith("xmlns:"):
            alias = attribute[len("xmlns:") :]
            url_to_alias[value] = alias
            alias_to_url[alias] = value
        else:
            # NOTE (mristin):
            # This attribute is otherwise irrelevant.
            pass

    if main is None:
        return None, "The main namespace is missing"

    return (
        _NamespaceDeclarations(
            main=main, url_to_alias=url_to_alias, alias_to_url=alias_to_url
        ),
        None,
    )


INDENT = "  "

# NOTE (mristin):
# The ElementTree library is very peculiar when it comes to namespaces. The namespace
# URLs are directly inserted as prefixes to tag names, even when the user specifies
# an alias.
_ET_NAMESPACE_PREFIX_RE = re.compile(r"^\{(?P<namespace>[^}]*)}")


def _render(
    element: ET.Element,
    writer: TextIO,
    namespace_declarations: _NamespaceDeclarations,
    level: int = 0,
) -> None:
    """
    Render the given XML tree starting with the ``element`` at the root.

    We designed the rendering such that the XMLs are easy to read and diff.
    """
    indention = INDENT * level

    if element.tag is ET.Comment:  # type: ignore
        writer.write(f"{indention}<!-- {element.text} -->\n")
    else:
        if len(element) > 0:
            if element.text is not None and not element.text.isspace():
                raise ValueError(
                    f"Unexpected element with children "
                    f"and non-whitespace text: {element}; "
                    f"the text was: {element.text!r}"
                )

            if element.tail is not None and not element.tail.isspace():
                raise ValueError(
                    f"Unexpected element with children "
                    f"and non-whitespace tail: {element}; "
                    f"the tail was: {element.tail!r}"
                )

        ns_match = _ET_NAMESPACE_PREFIX_RE.match(element.tag)
        if ns_match is not None:
            ns_url = ns_match.group("namespace")

            if ns_url == namespace_declarations.main:
                # NOTE (mristin):
                # We add 2 for the enclosing ``{`` and ``}``.
                name = element.tag[len(ns_url) + 2 :]
            else:
                ns_alias = namespace_declarations.url_to_alias.get(ns_url, None)
                if ns_alias is None:
                    raise ValueError(
                        f"Unexpected namespace URL in the ET element {element}. "
                        f"The declared namespaces aliases "
                        f"were: {namespace_declarations.url_to_alias}"
                    )

                # NOTE (mristin):
                # We add 2 for the enclosing ``{`` and ``}``.
                local_name = element.tag[len(ns_url) + 2 :]
                name = f"{ns_alias}:{local_name}"
        else:
            name = element.tag

        text = None  # type: Optional[str]
        if element.text is not None and not element.text.isspace():
            text = element.text

        if text is None and len(element) == 0:
            if len(element.attrib) == 0:
                writer.write(f"{indention}<{name} />\n")
            else:
                writer.write(f"{indention}<{name}\n")
                for attrib, value in element.attrib.items():
                    quoted_value = xml.sax.saxutils.quoteattr(value)
                    writer.write(f"{indention}{INDENT}{attrib}={quoted_value}\n")

                writer.write(f"{indention}/>\n")

        elif text is not None and len(element) == 0:
            escaped_text = xml.sax.saxutils.escape(text)

            if len(element.attrib) == 0:
                writer.write(f"{indention}<{name}>{escaped_text}</{name}>\n")
            else:
                writer.write(f"{indention}<{name}\n")

                for attrib, value in element.attrib.items():
                    quoted_value = xml.sax.saxutils.quoteattr(value)
                    writer.write(f"{indention}{INDENT}{attrib}={quoted_value}\n")

                writer.write(f"{indention}>{escaped_text}</{name}>\n")

        elif text is None and len(element) > 0:
            if len(element.attrib) == 0:
                writer.write(f"{indention}<{name}>\n")

                for child in element:
                    _render(
                        element=child,
                        writer=writer,
                        namespace_declarations=namespace_declarations,
                        level=level + 1,
                    )

                writer.write(f"{indention}</{name}>\n")
            else:
                writer.write(f"{indention}<{name}\n")

                for attrib, value in element.attrib.items():
                    quoted_value = xml.sax.saxutils.quoteattr(value)
                    writer.write(f"{indention}{INDENT}{attrib}={quoted_value}\n")

                writer.write(f"{indention}>\n")

                for child in element:
                    _render(
                        element=child,
                        writer=writer,
                        namespace_declarations=namespace_declarations,
                        level=level + 1,
                    )

                writer.write(f"{indention}</{name}>\n")

        else:
            raise AssertionError("Unexpected execution path")


@ensure(lambda result: not (result[1] is not None) or (len(result[1]) >= 1))
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(lambda result: not (result[0] is not None) or (result[0].endswith("\n")))
def _generate(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate tne node set according to the symbol table."""
    base_nodeset_key = specific_implementations.ImplementationKey("base_nodeset.xml")

    base_nodeset_text = spec_impls.get(base_nodeset_key, None)
    if base_nodeset_text is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the base OPC UA nodeset "
                f"is missing: {base_nodeset_key}",
            )
        ]

    name_prefix_key = specific_implementations.ImplementationKey("name_prefix.txt")

    name_prefix_text = spec_impls.get(name_prefix_key, None)
    if name_prefix_text is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the type name prefix "
                f"is missing: {name_prefix_key}",
            )
        ]

    if not IDENTIFIER_RE.match(name_prefix_text):
        return None, [
            Error(
                None,
                f"The implementation snippet for the type name prefix "
                f"at {name_prefix_key} is invalid: {name_prefix_text}",
            )
        ]

    name_prefix = Identifier(name_prefix_text)

    namespace_declarations, error = _extractNamespaceDeclarationsFromXML(
        base_nodeset_text
    )
    if error is not None:
        return None, [
            Error(
                None,
                f"The namespaces could not be extracted from the implementation snippet "
                f"for the base OPC UA nodeset {base_nodeset_key}: {error}",
            )
        ]

    assert namespace_declarations is not None

    if "uax" not in namespace_declarations.alias_to_url:
        return None, [
            Error(
                None,
                f"The namespace alias for 'uax' is missing in "
                f"the implementation snippet for the base OPC UA "
                f"nodeset: {base_nodeset_key}",
            )
        ]

    try:
        root = ET.fromstring(base_nodeset_text)
    except Exception as err:
        return None, [
            Error(
                None,
                f"Failed to parse the base nodeset XML out of "
                f"the snippet {base_nodeset_key}: {err}",
            )
        ]

    identifier_machine = _IdentifierMachine()

    identifier_map = (
        collections.OrderedDict()
    )  # type: MutableMapping[_OpcUaIdentifiable, int]

    root.append(_generate_aliases())

    # region Generate identifiers

    identifiers_for_constraints = _IdentifiersForConstraints(
        # NOTE (mristin):
        # We prefix here with ``_`` in order to avoid conflicts with AAS class names.
        constraint_id=identifier_machine.obtain("_Constraint"),
        constraint_identifier_id=identifier_machine.obtain("_Constraint.identifier"),
        constraint_text_id=identifier_machine.obtain("_Constraint.text"),
        has_constraint_id=identifier_machine.obtain("_HasConstraint"),
    )

    # noinspection SpellCheckingInspection
    invariants = [
        invariant
        for invariantable in itertools.chain(
            symbol_table.classes, symbol_table.constrained_primitives
        )
        for invariant in invariantable.invariants
        if invariant.specified_for is invariantable
    ]

    observed_invariant_uid_set = set()  # type: Set[str]

    for invariant in invariants:
        # NOTE (mristin):
        # We rely on
        # :py:func:`intermediate._translate._verify_invariant_descriptions_unique`
        # that the invariant descriptions are unique.

        invariant_uid = (
            f"{invariant.specified_for.name}" f":invariant:{invariant.description}"
        )

        assert (
            invariant_uid not in observed_invariant_uid_set
        ), f"Unexpected duplicate invariant ID for: {invariant_uid}"
        observed_invariant_uid_set.add(invariant_uid)

        identifier_map[invariant] = identifier_machine.obtain(invariant_uid)

    for enumeration in symbol_table.enumerations:
        identifier_map[enumeration] = identifier_machine.obtain(enumeration.name)

    for constrained_primitive in symbol_table.constrained_primitives:
        identifier_map[constrained_primitive] = identifier_machine.obtain(
            constrained_primitive.name
        )

    for cls in symbol_table.classes:
        if cls.interface is not None:
            identifier_map[cls.interface] = identifier_machine.obtain(
                # NOTE (mristin):
                # We prefix with ``interface:`` to avoid conflicts with
                # concrete classes.
                f"interface:{cls.name}"
            )

    for concrete_cls in symbol_table.concrete_classes:
        identifier_map[concrete_cls] = identifier_machine.obtain(concrete_cls.name)

    for cls in symbol_table.classes:
        for prop in cls.properties:
            if prop.specified_for is not cls:
                continue

            identifier_map[prop] = identifier_machine.obtain(f"{cls.name}.{prop.name}")

    # endregion

    root.extend(
        _generate_for_constraints_and_patterns(
            identifiers_for_constraints=identifiers_for_constraints
        )
    )

    if len(symbol_table.enumerations) > 0:
        root.append(ET.Comment("Enumerations start here."))

    for enumeration in symbol_table.enumerations:
        root.extend(
            _generate_for_enum(
                enumeration=enumeration,
                identifier_map=identifier_map,
                identifier_machine=identifier_machine,
                name_prefix=name_prefix,
            )
        )

    if len(symbol_table.enumerations) > 0:
        root.append(ET.Comment("Enumerations end here."))

    if len(invariants) > 0:
        root.append(ET.Comment("Constraints start here."))

    for invariant in invariants:
        root.extend(
            _generate_for_invariant(
                invariant=invariant,
                identifier_map=identifier_map,
                identifiers_for_constraints=identifiers_for_constraints,
                identifier_machine=identifier_machine,
            )
        )

    if len(invariants) > 0:
        root.append(ET.Comment("Constraints end here."))

    if len(symbol_table.constrained_primitives) > 0:
        root.append(ET.Comment("Constrained primitives start here."))

    for constrained_primitive in symbol_table.constrained_primitives:
        root.append(
            _generate_for_constrained_primitive(
                constrained_primitive=constrained_primitive,
                identifier_map=identifier_map,
                identifiers_for_constraints=identifiers_for_constraints,
                name_prefix=name_prefix,
            )
        )

    if len(symbol_table.constrained_primitives) > 0:
        root.append(ET.Comment("Constrained primitives end here."))

    for cls in symbol_table.classes:
        if cls.interface is not None:
            root.extend(
                _generate_for_interface(
                    interface=cls.interface,
                    identifier_map=identifier_map,
                    identifiers_for_constraints=identifiers_for_constraints,
                    name_prefix=name_prefix,
                )
            )

    for concrete_cls in symbol_table.concrete_classes:
        root.extend(
            _generate_for_concrete_class(
                cls=concrete_cls,
                identifier_map=identifier_map,
                identifiers_for_constraints=identifiers_for_constraints,
                name_prefix=name_prefix,
            )
        )

    writer = io.StringIO()

    # NOTE (mristin):
    # ElementTree removes the namespaces in the root, so we have to add them back
    # manually.
    root.attrib["xmlns"] = namespace_declarations.main
    for alias, url in namespace_declarations.alias_to_url.items():
        root.attrib[f"xmlns:{alias}"] = url

    _render(element=root, writer=writer, namespace_declarations=namespace_declarations)

    return writer.getvalue(), None


def execute(
    context: run.Context,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """
    Execute the generation with the given parameters.

    Return the error code, or 0 if no errors.
    """
    code, errors = _generate(
        symbol_table=context.symbol_table, spec_impls=context.spec_impls
    )
    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the OPC UA node set "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    # noinspection SpellCheckingInspection
    pth = context.output_dir / "nodeset.xml"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the OPC UA node set to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    stdout.write(f"Code generated to: {context.output_dir}\n")

    return 0
