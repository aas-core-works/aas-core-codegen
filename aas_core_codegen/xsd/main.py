"""Generate XML Schema Definition (XSD) corresponding to the meta-model."""
import re
import xml.etree.ElementTree as ET
from typing import TextIO, MutableMapping, Optional, Tuple, List, Sequence, Set, Union

# noinspection PyUnresolvedReferences
import xml.dom.minidom
from icontract import ensure

from aas_core_codegen import naming, specific_implementations, intermediate, run, \
    infer_for_schema
from aas_core_codegen.common import Error, assert_never
from aas_core_codegen.xsd import (
    naming as xsd_naming
)


def _define_for_enumeration(
        enumeration: intermediate.Enumeration
) -> List[ET.Element]:
    """
    Generate the definitions for an ``enumeration``.

    The root element is to be *extended* with the resulting list.
    """
    restriction = ET.Element("xs:restriction", {"base": "xs:string"})
    for literal in enumeration.literals:
        restriction.append(ET.Element("xs:enumeration", {"value": literal.value}))

    element = ET.Element("xs:simpleType",
                         {'name': xsd_naming.model_type(enumeration.name)})
    element.append(restriction)

    return [element]


_BUILTIN_MAP = {
    intermediate.BuiltinAtomicType.BOOL: "xs:boolean",
    intermediate.BuiltinAtomicType.INT: "xs:integer",
    intermediate.BuiltinAtomicType.FLOAT: "xs:double",
    intermediate.BuiltinAtomicType.STR: "xs:string",
    intermediate.BuiltinAtomicType.BYTEARRAY: "xs:base64Binary"
}
assert all(literal in _BUILTIN_MAP for literal in intermediate.BuiltinAtomicType)


def _define_for_property(
        prop: intermediate.Property,
        ref_association: intermediate.Symbol,
        len_constraint: Optional[infer_for_schema.LenConstraint],
        pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]]
) -> ET.Element:
    """Generate the definition of a property element."""
    type_anno = prop.type_annotation
    while isinstance(type_anno, intermediate.OptionalTypeAnnotation):
        type_anno = type_anno.value

    prop_element = None  # type: Optional[ET.Element]
    if isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
        if (
                pattern_constraints is not None
                and len(pattern_constraints) > 0
        ):
            prop_element = ET.Element(
                "xs:element", {"name": naming.xml_property(prop.name)})

            restriction = ET.Element(
                "xs:restriction", {"base": _BUILTIN_MAP[type_anno.a_type]})

            simple_type = ET.Element("xs:simpleType")
            simple_type.append(restriction)

            prop_element.append(simple_type)

            if len(pattern_constraints) == 1:
                pattern = ET.Element(
                    "xs:pattern", {"value": pattern_constraints[0].pattern})

                restriction.append(pattern)
            else:
                # TODO-BEFORE-RELEASE (mristin, 2021-12-13):
                #  test this and check that the XSD makes sense with somebody else!
                parent_restriction = restriction
                for pattern_constraint in pattern_constraints:
                    nested_restriction = ET.Element("xs:restriction")
                    pattern = ET.Element(
                        "xs:pattern", {"value": pattern_constraint.pattern})

                    nested_restriction.append(pattern)
                    parent_restriction.append(nested_restriction)
                    parent_restriction = nested_restriction
        else:
            prop_element = ET.Element(
                "xs:element",
                {
                    "name": naming.xml_property(prop.name),
                    "type": _BUILTIN_MAP[type_anno.a_type]
                })

    elif isinstance(type_anno, intermediate.OurAtomicTypeAnnotation):
        if isinstance(type_anno.symbol, (intermediate.Enumeration, intermediate.Class)):
            prop_element = ET.Element(
                "xs:element",
                {
                    "name": naming.xml_property(prop.name),
                    "type": xsd_naming.model_type(type_anno.symbol.name)
                })

        elif isinstance(type_anno.symbol, intermediate.Interface):
            prop_choice = ET.Element("xs:choice")
            prop_choice.append(
                ET.Element(
                    "xs:group",
                    {
                        "ref": xsd_naming.interface_abstract(type_anno.symbol.name)
                    }))

            prop_complex_type = ET.Element("xs:complexType")
            prop_complex_type.append(prop_choice)

            prop_element = ET.Element(
                "xs:element",
                {
                    "name": naming.xml_property(prop.name)
                })
            prop_element.append(prop_complex_type)

        else:
            assert_never(type_anno.symbol)

    elif isinstance(type_anno, intermediate.RefTypeAnnotation):
        if isinstance(type_anno.value, intermediate.OurAtomicTypeAnnotation):
            prop_element = ET.Element(
                "xs:element",
                {
                    "name": naming.xml_property(prop.name),
                    "type": xsd_naming.model_type(ref_association.name)
                })

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        list_element = None  # type: Optional[ET.Element]

        min_occurs = '0'
        max_occurs = 'unbounded'
        if len_constraint is not None:
            if len_constraint.min_value is not None:
                min_occurs = str(len_constraint.min_value)

            if len_constraint.max_value is not None:
                max_occurs = str(len_constraint.max_value)

        if isinstance(type_anno.items, intermediate.OurAtomicTypeAnnotation):
            # NOTE (mristin, 2021-11-13):
            # We need to nest the enumerations and concrete classes in the tag
            # element to delineate them in the sequence. On the other hand,
            # an interface already implies the tag element since interfaces need
            # to discriminate on the concrete classes.

            if isinstance(
                    type_anno.items.symbol,
                    (intermediate.Enumeration, intermediate.Class)):

                list_element = ET.Element("xs:sequence")
                list_element.append(ET.Element(
                    "xs:element",
                    {
                        "minOccurs": min_occurs,
                        "maxOccurs": max_occurs,
                        "name": naming.xml_class_name(type_anno.items.symbol.name),
                        "type": xsd_naming.model_type(type_anno.items.symbol.name)
                    }))

            elif isinstance(type_anno.items.symbol, intermediate.Interface):
                list_element = ET.Element(
                    "xs:choice",
                    {"minOccurs": min_occurs, "maxOccurs": max_occurs})

                list_element.append(
                    ET.Element("xs:group",
                               {
                                   "ref": xsd_naming.interface_abstract(
                                       type_anno.items.symbol.name)
                               }
                               ))

            else:
                assert_never(type_anno.items.symbol)

        elif isinstance(type_anno.items, intermediate.RefTypeAnnotation):
            list_element = ET.Element("xs:sequence")
            list_element.append(ET.Element(
                "xs:element",
                {
                    "minOccurs": min_occurs,
                    "maxOccurs": max_occurs,
                    "name": naming.xml_class_name(ref_association.name),
                    "type": xsd_naming.model_type(ref_association.name)
                }))

        else:
            # NOTE (mristin, 2021-11-28):
            # We did not implement this case yet as we lacked the context.
            pass

        if list_element is not None:
            prop_complex_type = ET.Element('xs:complexType')
            prop_complex_type.append(list_element)

            prop_element = ET.Element(
                "xs:element",
                {
                    "name": naming.xml_property(prop.name)
                })
            prop_element.append(prop_complex_type)

    if prop_element is None:
        raise NotImplementedError(
            f'(mristin, 2021-11-23):\n'
            f'We implemented only a subset of possible type annotations '
            f'to be represented in an XML Schema Definition since we lacked more '
            f'information about the context.\n\n'
            f'This feature needs yet to be implemented.\n\n'
            f'{type_anno=}')

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        prop_element.attrib['minOccurs'] = "0"

    return prop_element


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_properties(
        symbol: Union[intermediate.Interface, intermediate.Class],
        ref_association: intermediate.Symbol
) -> Tuple[Optional[List[ET.Element]], Optional[List[Error]]]:
    """Define the properties of the ``symbol`` as a sequence of tags."""
    len_constraints_by_property, len_constraints_errors = (
        infer_for_schema.infer_len_constraints(symbol=symbol))

    if len_constraints_errors is not None:
        return None, len_constraints_errors

    assert len_constraints_by_property is not None

    pattern_constraints_by_property = infer_for_schema.infer_pattern_constraints(
        symbol=symbol)

    sequence = []  # type: List[ET.Element]

    for prop in symbol.properties:
        if prop.implemented_for is not symbol:
            continue

        len_constraint = len_constraints_by_property.get(prop, None)
        pattern_constraints = pattern_constraints_by_property.get(prop, None)

        prop_element = _define_for_property(
            prop=prop,
            ref_association=ref_association,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints)

        sequence.append(prop_element)

    return sequence, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_for_interface(
        interface: intermediate.Interface,
        implementers: Sequence[intermediate.Class],
        ids_of_used_interfaces: Set[int],
        ref_association: intermediate.Symbol
) -> Tuple[Optional[List[ET.Element]], Optional[List[Error]]]:
    """
    Generate the definitions for the ``interface``.

    The root element is to be *extended* with the resulting list.
    """
    # region Part definition

    sequence = ET.Element("xs:sequence")

    for inheritance in interface.inheritances:
        inheritance_part = ET.Element(
            "xs:group",
            {"ref": xsd_naming.model_type(inheritance.name)})
        sequence.append(inheritance_part)

    properties, properties_errors = _define_properties(
        symbol=interface,
        ref_association=ref_association)

    if properties_errors is not None:
        return None, properties_errors

    assert properties is not None
    sequence.extend(properties)

    interface_group = ET.Element(
        "xs:group",
        {"name": xsd_naming.model_type(interface.name)})

    interface_group.append(sequence)

    # endregion

    result = [interface_group]

    if id(interface) in ids_of_used_interfaces:
        choice = ET.Element("xs:choice")
        for implementer in implementers:
            element = ET.Element(
                "xs:element",
                {
                    "name": naming.xml_class_name(implementer.name),
                    "type": xsd_naming.model_type(implementer.name)
                })
            choice.append(element)

        abstract_group = ET.Element(
            "xs:group",
            {"name": xsd_naming.interface_abstract(interface.name)})
        abstract_group.append(choice)

        result.append(abstract_group)

    return result, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_for_class(
        cls: intermediate.Class,
        ref_association: intermediate.Symbol
) -> Tuple[Optional[List[ET.Element]], Optional[List[Error]]]:
    """
    Generate the definitions for the class ``cls``.

    The root element is to be *extended* with the resulting list.
    """
    sequence = ET.Element("xs:sequence")

    for interface in cls.interfaces:
        interface_part = ET.Element(
            "xs:group",
            {"ref": xsd_naming.model_type(interface.name)})
        sequence.append(interface_part)

    properties, properties_errors = _define_properties(
        symbol=cls,
        ref_association=ref_association)

    if properties_errors is not None:
        return None, properties_errors

    assert properties is not None
    sequence.extend(properties)

    complex_type = ET.Element(
        "xs:complexType",
        {"name": xsd_naming.model_type(cls.name)})

    if len(sequence) > 0:
        complex_type.append(sequence)

    return [complex_type], None


_WHITESPACE_RE = re.compile(r'\s+')


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations,
        interface_implementers: intermediate.InterfaceImplementers
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the XML Schema Definition (XSD) based on the ``symbol_table."""
    root_element_key = specific_implementations.ImplementationKey("root_element.xml")

    root_element_as_text = spec_impls.get(root_element_key, None)
    if root_element_as_text is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the root element "
                f"is missing: {root_element_key}")]

    # noinspection PyUnusedLocal
    root = None  # type: Optional[ET.Element]
    try:
        root = ET.fromstring(root_element_as_text)
    except ET.ParseError as err:
        return None, [Error(
            None,
            f"Failed to parse the root element from {root_element_key}: {err}"
        )]

    assert root is not None

    errors = []  # type: List[Error]

    ids_of_used_interfaces = intermediate.collect_ids_of_interfaces_in_properties(
        symbol_table=symbol_table)

    for symbol in symbol_table.symbols:
        elements = None  # type: Optional[List[ET.Element]]

        if (
                isinstance(symbol, intermediate.Class)
                and symbol.is_implementation_specific
        ):
            implementation_key = specific_implementations.ImplementationKey(
                f"{symbol.name}.xml")

            text = spec_impls.get(implementation_key, None)
            if text is None:
                errors.append(Error(
                    symbol.parsed.node,
                    f"The implementation is missing "
                    f"for the implementation-specific class: {implementation_key}"))
                continue

            # noinspection PyUnusedLocal
            implementation_root = None  # type: Optional[ET.Element]

            try:
                implementation_root = ET.fromstring(text)
            except Exception as err:
                errors.append(Error(
                    symbol.parsed.node,
                    f"Failed to parse the XML out of "
                    f"the specific implementation {implementation_key}: {err}"
                ))
                continue

            assert implementation_root is not None

            # Prepare for pretty-print later
            for descendant in implementation_root.iter():
                if descendant.text is not None:
                    assert _WHITESPACE_RE.fullmatch(descendant.text), (
                        f"Expected text of a node to be all whitespace, "
                        f"but got: {descendant.text}")
                    descendant.text = ''

                if descendant.tail is not None:
                    assert _WHITESPACE_RE.fullmatch(descendant.tail), (
                        f"Expected text of a node to be all whitespace, "
                        f"but got: {descendant.tail}")

                    descendant.tail = ''

            # Ignore the implementation root since it defines a partial schema
            elements = []
            for child in implementation_root:
                elements.append(child)
        else:
            if isinstance(symbol, intermediate.Enumeration):
                elements = _define_for_enumeration(enumeration=symbol)

            elif isinstance(symbol, intermediate.Interface):
                elements, definition_errors = _define_for_interface(
                    interface=symbol,
                    implementers=interface_implementers.get(symbol, []),
                    ids_of_used_interfaces=ids_of_used_interfaces,
                    ref_association=symbol_table.ref_association)

                if definition_errors is not None:
                    errors.extend(definition_errors)
                    continue

            elif isinstance(symbol, intermediate.Class):
                elements, definition_errors = _define_for_class(
                    cls=symbol,
                    ref_association=symbol_table.ref_association)

                if definition_errors is not None:
                    errors.extend(definition_errors)
                    continue
            else:
                assert_never(symbol)

        assert elements is not None
        root.extend(elements)

    if len(errors) > 0:
        return None, errors

    observed_definitions = dict()  # type: MutableMapping[str, ET.Element]
    for element in root:
        name = element.attrib.get('name', None)
        if name is None:
            continue

        observed = observed_definitions.get(name, None)
        if observed is not None:
            ours = ET.tostring(element, encoding='unicode', method='xml')
            theirs = ET.tostring(observed, encoding='unicode', method='xml')

            errors.append(Error(
                None,
                f"There are conflicting definitions in the schema "
                f"with the name {name!r}:\n"
                f"\n"
                f"{ours}\n"
                f"\n"
                f"and\n"
                f"\n"
                f"{theirs}"))
        else:
            observed_definitions[name] = element

    if len(errors) > 0:
        return None, errors

    text = ET.tostring(root, encoding='unicode', method='xml')

    # NOTE (mristin, 2021-11-23):
    # This approach is slow, but effective. As long as the meta-model is not too big,
    # this should work.
    # noinspection PyUnresolvedReferences
    pretty_text = xml.dom.minidom.parseString(text).toprettyxml(indent='  ')

    return pretty_text, None


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    code, errors = _generate(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        interface_implementers=context.interface_implementers)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the XML Schema Definition "
                    f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = context.output_dir / "schema.xml"
    try:
        pth.write_text(code)
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the XML Schema Definition to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
