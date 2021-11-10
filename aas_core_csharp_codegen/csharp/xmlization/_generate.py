"""Generate C# code for XML-ization based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List

from icontract import ensure, require

from aas_core_csharp_codegen import intermediate, specific_implementations, naming
from aas_core_csharp_codegen.common import Error, Stripped, Identifier, \
    assert_never
from aas_core_csharp_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
    unrolling as csharp_unrolling
)
# TODO: apply this trick to everything
from aas_core_csharp_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III
)


@require(lambda cls: cls.xml_serialization.property_as_text is not None)
def _generate_serialization_with_property_as_text(
        cls: intermediate.Class
) -> Stripped:
    """Generate the serialization body for ``cls`` with ``property_as_text``."""
    xml_name = naming.xml_name(cls.name)

    prop_as_text = None  # type: Optional[intermediate.Property]
    props_as_attributes = []  # type: List[intermediate.Property]

    for prop in cls.properties:
        if prop.name == cls.xml_serialization.property_as_text:
            prop_as_text = prop
        else:
            props_as_attributes.append(prop)

    assert prop_as_text is not None

    blocks = [
        Stripped(textwrap.dedent(f'''\
            // Main tag
            _writer.WriteStartElement({csharp_common.string_literal(xml_name)});'''))
    ]

    for prop in props_as_attributes:
        xml_attr = naming.xml_attribute(prop.name)
        prop_name = csharp_naming.property_name(prop.name)

        if isinstance(prop.type_annotation, intermediate.BuiltinAtomicTypeAnnotation):
            blocks.append(Stripped(textwrap.dedent(f'''\
                // Serialize {prop_name}
                _writer.WriteStartAttribute({csharp_common.string_literal(xml_attr)});
                _writer.WriteValue(that.{prop_name});
                _writer.WriteEndAttribute();''')))

        elif isinstance(prop.type_annotation, intermediate.OurAtomicTypeAnnotation):
            if isinstance(prop.type_annotation.symbol, intermediate.Enumeration):
                enum_name = csharp_naming.enum_name(prop.type_annotation.symbol.name)

                blocks.append(Stripped(textwrap.dedent(f'''\
                    // Serialize {prop_name}
                    _writer.WriteStartAttribute({csharp_common.string_literal(xml_attr)});
                    _writer.WriteValue(
                    {I}Stringification.ToString(that.{prop_name})
                    {II}?? throw new System.ArgumentException(
                    {III}$"Invalid {enum_name}: {{that.{prop_name}}}");
                    _writer.WriteEndAttribute();''')))
            else:
                raise AssertionError(prop.type_annotation.symbol)
        else:
            raise AssertionError(prop.type_annotation)

    prop_as_text_name = csharp_naming.property_name(prop_as_text.name)

    if isinstance(
            prop_as_text.type_annotation, intermediate.BuiltinAtomicTypeAnnotation):
        blocks.append(Stripped(textwrap.dedent(f'''\
                _writer.WriteValue(that.{prop_as_text_name});''')))
    elif isinstance(
            prop_as_text.type_annotation, intermediate.OurAtomicTypeAnnotation):
        if isinstance(prop_as_text.type_annotation.symbol, intermediate.Enumeration):
            enum_name = csharp_naming.enum_name(
                prop_as_text.type_annotation.symbol.name)

            var_name = csharp_naming.variable_name(
                Identifier(f"the_{prop_as_text.name}"))

            blocks.append(Stripped(textwrap.dedent(f'''\
                string {var_name} = Stringification.ToString(that.{prop_as_text_name})
                {I}?? throw new System.ArgumentException(
                {II}$"Invalid {enum_name}: {{that.{prop_as_text_name}}}");
                _writer.WriteValue({var_name});''')))
        else:
            raise AssertionError(prop_as_text.type_annotation.symbol)
    else:
        raise AssertionError(prop_as_text.type_annotation)

    blocks.append(Stripped(textwrap.dedent('''\
        // Main tag
        _writer.WriteEndElement();''')))

    return Stripped('\n\n'.join(blocks))


@require(lambda cls: cls.xml_serialization.property_as_text is None)
def _generate_serialization(
        cls: intermediate.Class
) -> Stripped:
    """Generate the serialization body for ``cls`` with default settings."""
    xml_name = naming.xml_name(cls.name)

    blocks = [
        Stripped(textwrap.dedent(f'''\
            // Main tag
            _writer.WriteStartElement({csharp_common.string_literal(xml_name)});'''))
    ]  # type: List[Stripped]

    for prop in cls.properties:
        prop_name = csharp_naming.property_name(prop.name)
        xml_attr = naming.xml_attribute(prop.name)

        stmts = [
            Stripped(f"// Serialize {prop_name}")
        ]

        # region Unroll

        @require(lambda var_index: var_index >= 0)
        def var_name(var_index: int) -> Identifier:
            """Generate the name of the loop variable."""
            if var_index == 0:
                return Identifier(f"anItem")
            elif var_index == 1:
                return Identifier(f"anotherItem")
            else:
                return Identifier("yet" + "Yet" * (var_index - 1) + f"anotherItem")

        def unroll(
                current_var_name: str,
                item_count: int,
                type_anno: intermediate.TypeAnnotation
        ) -> List[csharp_unrolling.Node]:
            """Generate the serialization for the ``type_anno`` and recurse."""
            if isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
                if item_count == 0:
                    # We are at the root level of the property.
                    assert current_var_name == f'that.{prop_name}'

                    return [csharp_unrolling.Node(
                        text=Stripped(textwrap.dedent(f'''\
                            _writer.WriteStartElement({csharp_common.string_literal(xml_attr)});
                            _writer.WriteValue({current_var_name});
                            _writer.WriteEndElement();''')),
                        children=[]
                    )]
                else:
                    raise NotImplementedError(
                        f"(mristin, 2021-11-10):\n"
                        f"We did not implement an XML serialization "
                        f"of atomic built-in values in a descendable property. "
                        f"The property was {prop.name} of entity {cls.parsed.name}. "
                        f"Please have a closer look and implement this feature "
                        f"once the context is more clear.\n\n"
                        f"{type_anno=}, {item_count=}, {current_var_name=}")

            elif isinstance(type_anno, intermediate.OurAtomicTypeAnnotation):
                if isinstance(type_anno.symbol, intermediate.Enumeration):
                    if item_count == 0:
                        # We are at the root level of the property.
                        assert current_var_name == f'that.{prop_name}'

                        enum_name = csharp_naming.enum_name(type_anno.symbol.name)

                        return [csharp_unrolling.Node(
                            text=Stripped(textwrap.dedent(f'''\
                                _writer.WriteStartElement({csharp_common.string_literal(xml_attr)});
                                _writer.WriteValue(
                                {I}Stringification.ToString({current_var_name})
                                {II}?? throw new System.ArgumentException(
                                {III}$"Invalid {enum_name}: {{{current_var_name}}}"));
                                _writer.WriteEndElement();''')),
                            children=[]
                        )]
                    else:
                        raise NotImplementedError(
                            f"(mristin, 2021-11-10):\n"
                            f"We did not implement an XML serialization "
                            f"of enumerations in a descendable property. "
                            f"The property was {prop.name} of "
                            f"entity {cls.parsed.name}. Please have a closer look "
                            f"and implement this feature once the context is "
                            f"more clear.\n\n"
                            f"{type_anno=}, {item_count=}, {current_var_name=}")

                elif isinstance(
                        type_anno.symbol,
                        (intermediate.Interface, intermediate.Class)):
                    if item_count == 0:
                        # We are at the root level of the property.
                        return [csharp_unrolling.Node(
                            text=Stripped(textwrap.dedent(f'''\
                                _writer.WriteStartElement({csharp_common.string_literal(xml_attr)});
                                Visit({current_var_name});
                                _writer.WriteEndElement();''')),
                            children=[])]
                    else:
                        return [csharp_unrolling.Node(
                            f'Visit({current_var_name});', children=[])]

            elif isinstance(type_anno, (
                    intermediate.ListTypeAnnotation,
                    intermediate.SequenceTypeAnnotation,
                    intermediate.SetTypeAnnotation)):
                item_var = var_name(item_count)

                children = unroll(
                    current_var_name=var_name(item_count),
                    item_count=item_count + 1,
                    type_anno=type_anno.items)

                assert len(children) > 0, (
                    f"Expected children when unrolling: "
                    f"{prop=}, {cls=}, {item_count=}, {type_anno=}")

                node = csharp_unrolling.Node(
                    text=f"foreach (var {item_var} in {current_var_name})",
                    children=children)

                if item_count == 0:
                    return [
                        csharp_unrolling.Node(
                            text=f"_writer.WriteStartElement("
                                 f"{csharp_common.string_literal(xml_attr)});",
                            children=[]),
                        node,
                        csharp_unrolling.Node(
                            text=f"_writer.WriteEndElement();",
                            children=[]),
                    ]
                else:
                    return [node]

            elif isinstance(type_anno, (
                    intermediate.MappingTypeAnnotation,
                    intermediate.MutableMappingTypeAnnotation
            )):
                raise NotImplementedError(
                    f"(mristin, 2021-11-10):\n"
                    f"We did not implement an XML serialization "
                    f"of dictionaries in a descendable property. "
                    f"The property was {prop.name} of "
                    f"entity {cls.parsed.name}. Please have a closer look "
                    f"and implement this feature once the context is "
                    f"more clear.\n\n"
                    f"{type_anno=}, {item_count=}, {current_var_name=}")

            elif isinstance(type_anno, intermediate.OptionalTypeAnnotation):
                children = unroll(
                    current_var_name=current_var_name,
                    item_count=item_count,
                    type_anno=type_anno.value)

                assert len(children) > 0, (
                    f"Expected children when unrolling: "
                    f"{prop=}, {cls=}, {item_count=}, {type_anno=}")

                return [csharp_unrolling.Node(
                    text=f"if ({current_var_name} != null)", children=children)]
            else:
                assert_never(type_anno)

        roots = unroll(
            current_var_name=f"that.{prop_name}",
            item_count=0,
            type_anno=prop.type_annotation)

        assert len(roots) > 0, (
            f"Expected at least one unrolling root since "
            f"the property of the class {cls.name} "
            f"was descendable: {prop.name}")

        stmts.extend(Stripped(csharp_unrolling.render(root)) for root in roots)

        stmts.append(Stripped(f'// Serialized {prop_name}.'))

        # endregion

        blocks.append(Stripped('\n'.join(stmts)))

    blocks.append(Stripped(textwrap.dedent('''\
        // Main tag
        _writer.WriteEndElement();''')))

    return Stripped('\n\n'.join(blocks))


def _generate_serializer_visit(
        cls: intermediate.Class
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the serialization method for the intermediate class ``cls``."""
    blocks = []  # type: List[Stripped]

    if cls.xml_serialization.property_as_text is not None:
        blocks.append(_generate_serialization_with_property_as_text(cls=cls))
    else:
        blocks.append(_generate_serialization(cls=cls))

    cls_name = csharp_naming.class_name(cls.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public void Visit({cls_name} that) 
        {{
        '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, I))

    writer.write('\n}')

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_serializer(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    errors = []  # type: List[Error]

    blocks = [
        Stripped('private readonly Xml.XmlWriter _writer;'),
        Stripped(textwrap.dedent(f'''\
            Serializer(Xml.XmlWriter writer)
            {{
            {I}_writer = writer;
            }}''')),
        Stripped(textwrap.dedent(f'''\
            public void Visit(IEntity that)
            {{
            {I}that.Accept(this);
            }}'''))
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.Class):
            continue

        block = None  # type: Optional[Stripped]
        if symbol.is_implementation_specific:
            implementation_key = specific_implementations.ImplementationKey(
                f'Xmlization/Serializer/visit_{symbol.name}')

            implementation = spec_impls.get(implementation_key, None)
            if implementation is None:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"The xmlization serializer snippet is missing "
                        f"for the implementation-specific "
                        f"class {symbol.name}: {implementation_key}"))
                continue

            block = implementation
        else:
            block, error = _generate_serializer_visit(
                cls=symbol)
            if error is not None:
                errors.append(error)
                continue

        assert block is not None
        blocks.append(block)

    writer = io.StringIO()
    writer.write(textwrap.dedent('''\
        public class Serializer : Visitation.Visitor 
        {'''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, I))

    writer.write('\n}  // public class Serializer')

    return Stripped(writer.getvalue()), None


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
        symbol_table: intermediate.SymbolTable,
        namespace: csharp_common.NamespaceIdentifier,
        interface_implementers: intermediate.InterfaceImplementers,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code for the general serialization.

    The ``namespace`` defines the AAS C# namespace.
    """
    errors = []  # type: List[Error]

    blocks = [
        csharp_common.WARNING,
        Stripped(textwrap.dedent(f"""\
            /*
             * We implement a streaming-based XML de/serialization with 
             * <see cref="System.Xml.XmlReader" /> and <see cref="System.Xml.XmlWriter" /> 
             * due to performance reasons.
             * For more information, see:
             * <ul>
             * <li>https://bertwagner.com/posts/xmlreader-vs-xmldocument-performance/</li>
             * <li>https://www.erikthecoder.net/2019/08/02/xml-parsing-performance-csharp-versus-go/</li>
             * <li>https://docs.microsoft.com/en-us/dotnet/standard/serialization/xml-serializer-generator-tool-sgen-exe</li>
             * </ul>
             */""")),
        Stripped(textwrap.dedent(f"""\
            using Xml = System.Xml;
            using System.Collections.Generic;  // can't alias

            using Aas = {namespace};
            using Visitation = {namespace}.Visitation;"""))
    ]

    xmlization_blocks = []  # type: List[Stripped]

    serializer_code, serializer_errors = _generate_serializer(
        symbol_table=symbol_table,
        spec_impls=spec_impls
    )
    if serializer_errors is not None:
        errors.extend(serializer_errors)
    else:
        xmlization_blocks.append(serializer_code)

    # TODO: uncomment once implemented
    # deserializer_code, deserializer_errors = _generate_deserializer(
    #     symbol_table=symbol_table,
    #     interface_implementers=interface_implementers,
    #     spec_impls=spec_impls
    # )
    # if deserializer_errors is not None:
    #     errors.extend(deserializer_errors)
    # else:
    #     xmlization_blocks.append(serializer_code)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    # TODO: add better documentation!
    # TODO: add methods for starting a document and adding all the namespaces
    # TODO: also, Environment needs to be implementation-specific as its tag and namespaces
    #  are pretty out-of-ordinary!
    writer.write(textwrap.dedent(f'''\
        namespace {namespace}
        {{
        {I}public static class Xmlization
        {I}{{
        '''))

    for i, xmlization_block in enumerate(xmlization_blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(xmlization_block, II))

    writer.write(
        f"\n{I}}}  // public static class Xmlization")
    writer.write(f"\n}}  // namespace {namespace}")

    blocks.append(Stripped(writer.getvalue()))

    blocks.append(csharp_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write('\n\n')

        assert not block.startswith('\n')
        assert not block.endswith('\n')
        out.write(block)

    out.write('\n')

    return out.getvalue(), None
