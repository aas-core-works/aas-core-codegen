"""Generate XML Schema Definition (XSD) corresponding to the meta-model."""
import re
import xml.etree.ElementTree as ET
from typing import TextIO, MutableMapping, Optional, Tuple, List, Sequence

# noinspection PyUnresolvedReferences
import xml.dom.minidom
from icontract import ensure

from aas_core_codegen import naming, specific_implementations, intermediate, run
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
        prop: intermediate.Property
) -> ET.Element:
    """Generate the definition of a property element."""
    type_anno = prop.type_annotation
    while isinstance(type_anno, intermediate.OptionalTypeAnnotation):
        type_anno = type_anno.value

    prop_element = None  # type: Optional[ET.Element]
    if isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
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

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        if isinstance(type_anno.items, intermediate.OurAtomicTypeAnnotation):
            # NOTE (mristin, 2021-11-13):
            # We need to nest the enumerations and concrete classes in the tag
            # element to delineate them in the sequence. On the other hand,
            # an interface already implies the tag element since interfaces need
            # to discriminate on the concrete classes.

            list_element = None  # type: Optional[ET.Element]

            if isinstance(
                    type_anno.items.symbol,
                    (intermediate.Enumeration, intermediate.Class)):

                list_element = ET.Element("xs:sequence")
                list_element.append(ET.Element(
                    "xs:element",
                    {
                        "minOccurs": "0",
                        "maxOccurs": "unbounded",
                        "name": naming.xml_class_name(type_anno.items.symbol.name),
                        "type": xsd_naming.model_type(type_anno.items.symbol.name)
                    }))

            elif isinstance(type_anno.items.symbol, intermediate.Interface):
                list_element = ET.Element(
                    "xs:choice",
                    {"minOccurs": "0", "maxOccurs": "unbounded"})

                list_element.append(
                    ET.Element("xs:group",
                        {
                            "ref": xsd_naming.interface_abstract(
                                type_anno.items.symbol.name)
                        }
                    ))

            else:
                assert_never(type_anno.items.symbol)

            assert list_element is not None

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


def _define_for_interface(
        interface: intermediate.Interface,
        implementers: Sequence[intermediate.Class]
) -> List[ET.Element]:
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

    for prop in interface.properties:
        if prop.implemented_for is not interface:
            continue

        prop_element = _define_for_property(prop=prop)

        sequence.append(prop_element)

    interface_group = ET.Element(
        "xs:group",
        {"name": xsd_naming.model_type(interface.name)})

    interface_group.append(sequence)

    # endregion

    # region Define interface as choice of concrete classes

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

    # endregion

    return [interface_group, abstract_group]


def _define_for_class(
        cls: intermediate.Class
) -> List[ET.Element]:
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

    for prop in cls.properties:
        if prop.implemented_for is not cls:
            continue

        prop_element = _define_for_property(prop=prop)

        sequence.append(prop_element)

    complex_type = ET.Element(
        "xs:complexType",
        {"name": xsd_naming.model_type(cls.name)})

    if len(sequence) > 0:
        complex_type.append(sequence)

    return [complex_type]


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
                elements = _define_for_interface(
                    interface=symbol,
                    implementers=interface_implementers.get(symbol, []))

            elif isinstance(symbol, intermediate.Class):
                elements = _define_for_class(cls=symbol)

            else:
                assert_never(symbol)

        assert elements is not None
        root.extend(elements)

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
