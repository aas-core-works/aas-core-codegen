"""Generate C# code for JSON-ization based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List, Sequence

from icontract import ensure, require

from aas_core_csharp_codegen import intermediate, naming, specific_implementations
from aas_core_csharp_codegen.common import Error, Stripped, Identifier, \
    indent_but_first_line
from aas_core_csharp_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming
)
# TODO: apply this trick to everything
from aas_core_csharp_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII
)


def _generate_json_converter_for_enumeration(
        enumeration: intermediate.Enumeration
) -> Stripped:
    """Generate the custom JSON converter based on the intermediate ``enumeration``."""
    enum_name = csharp_naming.enum_name(enumeration.name)

    return Stripped(textwrap.dedent(f'''\
        public class {enum_name}JsonConverter :
        {I}System.Text.Json.Serialization.JsonConverter<Aas.{enum_name}>
        {{
        {I}public override Aas.{enum_name} Read(
        {II}ref System.Text.Json.Utf8JsonReader reader,
        {II}System.Type typeToConvert,
        {II}System.Text.Json.JsonSerializerOptions options)
        {I}{{
        {II}if (reader.TokenType != System.Text.Json.JsonTokenType.String)
        {II}{{
        {III}throw new System.Text.Json.JsonException();
        {II}}}
        
        {II}string? text = reader.GetString();
        {II}if (text == null)
        {II}{{
        {III}throw new System.Text.Json.JsonException();
        {II}}}
        
        {II}Aas.{enum_name}? value = Stringification.{enum_name}FromString(
        {III}text);
        {II}return value ?? throw new System.Text.Json.JsonException(
        {III}$"Invalid {enum_name}: {{text}}");
        {I}}}
        
        {I}public override void Write(
        {II}System.Text.Json.Utf8JsonWriter writer,
        {II}Aas.{enum_name} value,
        {II}System.Text.Json.JsonSerializerOptions options)
        {I}{{
        {II}string? text = Stringification.ToString(value);
        {II}if (text == null)
        {II}{{
        {III}throw new System.ArgumentException(
        {IIII}$"Invalid {enum_name}: {{value}}");
        {II}}}
        
        {II}writer.WriteStringValue(text);
        {I}}}
        }}'''))


# fmt: off
@require(
    lambda interface, implementers:
    all(
        interface.name in implementer.interfaces
        for implementer in implementers
    )
)
# fmt: on
def _generate_read_for_interface(
        interface: intermediate.Interface,
        implementers: Sequence[intermediate.Class]
) -> Stripped:
    """Generate the body of the ``Read`` method for de-serializing the ``interface``."""
    # TODO: for interface
    #  * allow converters only for interfaces with with_model_type
    #  * collect the union of the properties of the implementers
    #  🠒 make sure no duplicates!
    #  🠒 make sure all the type annotations are equal!
    #  * initialize all the properties (including modelType) to null
    #  * once endobject:
    #    * switch on modelType 🠒 return the constructor

    raise NotImplementedError()


def _generate_json_converter_for_interface(
        interface: intermediate.Interface,
        implementers: Sequence[intermediate.Class]
) -> Stripped:
    """Generate the custom JSON converter based on the intermediate ``interface``."""
    interface_name = csharp_naming.interface_name(interface.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
            public class {interface_name}JsonConverter :
            {I}System.Text.Json.Serialization.JsonConverter<Aas.{interface_name}>
            {{
            '''))

    writer.write(
        textwrap.indent(
            _generate_read_for_interface(
                interface=interface, implementers=implementers),
            csharp_common.INDENT))

    writer.write('\n\n')

    writer.write(
        textwrap.indent(
            _generate_write_for_interface(
                interface=interface, implementers=implementers),
            csharp_common.INDENT))

    writer.write(f'\n}}  // {interface_name}JsonConverter')

    return Stripped(writer.getvalue())


def _generate_read_for_class(
        cls: intermediate.Class
) -> Stripped:
    """Generate the body of the ``Read`` method for de-serializing the class ``cls``."""
    cls_name = csharp_naming.class_name(cls.name)

    blocks = [
        Stripped(textwrap.dedent(f'''\
            if (reader.TokenType != System.Text.Json.JsonTokenType.StartObject)
            {{
            {I}throw new System.Text.Json.JsonException();
            }}'''))
    ]

    # region Initializations

    if len(cls.properties) > 0:

        initialization_lines = [
            Stripped('// Prefix the property variables with "the" to avoid conflicts')
        ]  # type: List[Stripped]

        for prop in cls.properties:
            var_name = csharp_naming.variable_name(Identifier(f'the_{prop.name}'))
            prop_type = csharp_common.generate_type(prop.type_annotation)

            if prop_type.endswith('?'):
                initialization_lines.append(Stripped(
                    f'{prop_type} {var_name} = null;'))
            else:
                initialization_lines.append(Stripped(
                    f'{prop_type}? {var_name} = null;'))

        blocks.append('\n'.join(initialization_lines))

    # endregion

    # region Final successful case

    return_writer = io.StringIO()
    if len(cls.properties) > 0:
        return_writer.write(f'return new Aas.{cls_name}(\n')

        constructor_arg_names = [arg.name for arg in cls.constructor.arguments]
        assert (
                sorted(constructor_arg_names) ==
                sorted(prop.name for prop in cls.properties)
        ), "Expected the properties to match the constructor arguments"

        for i, constructor_arg_name in enumerate(constructor_arg_names):
            prop = cls.properties_by_name[constructor_arg_name]

            var_name = csharp_naming.variable_name(
                Identifier(f'the_{prop.name}'))

            if not isinstance(
                    prop.type_annotation, intermediate.OptionalTypeAnnotation):
                json_prop_name = naming.json_property(
                    Identifier(f'the_{prop.name}'))

                error_msg = csharp_common.string_literal(
                    f'Required property is missing: {json_prop_name}')

                return_writer.write(
                    textwrap.indent(
                        textwrap.dedent(f'''\
                            {var_name} ?? throw new System.Text.Json.JsonException(
                            {I}{error_msg})'''),
                        csharp_common.INDENT))
            else:
                return_writer.write(f'{I}{var_name}')

            if i < len(constructor_arg_names) - 1:
                return_writer.write(',\n')
            else:
                return_writer.write(');')

    else:
        return_writer.write(f'{I}return new Aas.{cls_name}();')

    # endregion

    # region Loop and switch

    token_case_blocks = [
        Stripped(f'''\
case System.Text.Json.JsonTokenType.EndObject:
{I}{indent_but_first_line(return_writer.getvalue(), I)}''')]

    if len(cls.properties) > 0 or cls.json_serialization.with_model_type:
        property_switch_writer = io.StringIO()
        property_switch_writer.write(textwrap.dedent(f'''\
            string propertyName = reader.GetString()
            {I}?? throw new System.InvalidOperationException(
            {II}"Unexpected property name null");

            switch (propertyName)
            {{
            '''))

        for prop in cls.properties:
            var_name = csharp_naming.variable_name(Identifier(f'the_{prop.name}'))

            if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
                prop_type = csharp_common.generate_type(prop.type_annotation.value)
            else:
                prop_type = csharp_common.generate_type(prop.type_annotation)

            json_prop_name = naming.json_property(prop.name)

            property_switch_writer.write(textwrap.indent(textwrap.dedent(f'''\
                case {csharp_common.string_literal(json_prop_name)}: 
                {I}{var_name} =  (
                {II}System.Text.Json.JsonSerializer.Deserialize<{prop_type}>(
                {III}ref reader));
                {I}break;
                '''), csharp_common.INDENT))

        if cls.json_serialization.with_model_type:
            property_switch_writer.write(textwrap.indent(textwrap.dedent(f'''\
                case "modelType": 
                    {I}// Ignore the property modelType as we already know the exact type
                    {I}break;
                    '''), csharp_common.INDENT))

        property_switch_writer.write(textwrap.dedent(f'''\
            {I}default:
            {II}throw new System.Text.Json.JsonException(
            {III}$"Unexpected property in {cls_name}: {{propertyName}}");
            }}  // switch on propertyName'''))

        token_case_blocks.append(Stripped(f'''\
case System.Text.Json.JsonTokenType.PropertyName:
{I}{indent_but_first_line(property_switch_writer.getvalue(), I)}
{I}break;'''))

    token_case_blocks.append(Stripped(textwrap.dedent(f'''\
        default:
        {I}throw new System.Text.Json.JsonException();''')))

    while_writer = io.StringIO()
    while_writer.write(textwrap.dedent(f'''\
        while (reader.Read())
        {{
        {I}switch (reader.TokenType)
        {I}{{
        '''))

    for i, token_case_block in enumerate(token_case_blocks):
        if i > 0:
            while_writer.write('\n\n')

        while_writer.write(textwrap.indent(token_case_block, csharp_common.INDENT2))

    while_writer.write(
        f'\n'
        f'{I}}}  // switch on token type\n'
        f'}}  // while reader.Read')

    blocks.append(Stripped(while_writer.getvalue()))

    blocks.append(Stripped('throw new System.Text.Json.JsonException();'))

    # endregion

    # region Bundle it all together

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public override Aas.{cls_name} Read(
        {I}ref System.Text.Json.Utf8JsonReader reader,
        {I}System.Type typeToConvert,
        {I}System.Text.Json.JsonSerializerOptions options)
        {{
        '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')
        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}')

    # endregion

    return Stripped(writer.getvalue())


def _generate_write_for_class(
        cls: intermediate.Class
) -> Stripped:
    """Generate the body of the ``Write`` method for serializing the class ``cls``."""
    blocks = [Stripped('writer.WriteStartObject();')]

    for prop in cls.properties:
        prop_name = csharp_naming.property_name(prop.name)
        json_prop_name = naming.json_property(prop.name)

        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            blocks.append(Stripped(textwrap.dedent(f'''\
                writer.WritePropertyName({csharp_common.string_literal(json_prop_name)});
                System.Text.Json.JsonSerializer.Serialize(
                {I}writer, that.{prop_name});''')))
        else:
            blocks.append(Stripped(textwrap.dedent(f'''\
                if (that.{prop_name} != null)
                {{
                {I}writer.WritePropertyName({csharp_common.string_literal(json_prop_name)});
                {I}System.Text.Json.JsonSerializer.Serialize(
                {II}writer, that.{prop_name});
                }}''')))

    blocks.append(Stripped('writer.WriteEndObject();'))

    # region Bundle it all together

    cls_name = csharp_naming.class_name(cls.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public override void Write(
        {I}System.Text.Json.Utf8JsonWriter writer,
        {I}Aas.{cls_name} that,
        {I}System.Text.Json.JsonSerializerOptions options)
        {{
        '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')
        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}')

    # endregion

    return Stripped(writer.getvalue())


def _generate_json_converter_for_class(
        cls: intermediate.Class
) -> Stripped:
    """Generate the custom JSON converter based on the intermediate ``cls``."""

    cls_name = csharp_naming.class_name(cls.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public class {cls_name}JsonConverter :
        {I}System.Text.Json.Serialization.JsonConverter<Aas.{cls_name}>
        {{
        '''))

    writer.write(
        textwrap.indent(
            _generate_read_for_class(cls=cls),
            csharp_common.INDENT))

    writer.write('\n\n')

    writer.write(
        textwrap.indent(
            _generate_write_for_class(cls=cls),
            csharp_common.INDENT))

    writer.write(f'\n}}  // {cls_name}JsonConverter')

    return Stripped(writer.getvalue())


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
             * For more information about customizing JSON serialization in C#, please see:
             * <ul>
             * <li>https://docs.microsoft.com/en-us/dotnet/standard/serialization/system-text-json-converters-how-to</li>
             * <li>https://docs.microsoft.com/en-gb/dotnet/standard/serialization/system-text-json-migrate-from-newtonsoft-how-to</li>
             * </ul>
             */""")),
        Stripped(textwrap.dedent(f"""\
            using System.Collections.Generic;  // can't alias

            using Aas = {namespace};"""))
    ]

    jsonization_blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        jsonization_block = None  # type: Optional[Stripped]
        if isinstance(symbol, intermediate.Enumeration):
            jsonization_block = _generate_json_converter_for_enumeration(
                enumeration=symbol)
        elif (
                isinstance(symbol, intermediate.Interface)
                and symbol.json_serialization.with_model_type
        ):
            # Only interfaces with ``modelType`` property can be deserialized as
            # otherwise we would lack the discriminating property.
            implementers = interface_implementers[symbol]
            jsonization_block = _generate_json_converter_for_interface(
                interface=symbol,
                implementers=implementers)

        elif isinstance(symbol, intermediate.Class):
            if symbol.implementation_key is not None:
                jsonization_key = specific_implementations.ImplementationKey(
                    f'Jsonization/{symbol.name}_json_converter')
                if jsonization_key not in spec_impls:
                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The jsonization snippet is missing "
                            f"for the implementation-specific "
                            f"class {symbol.name}: {jsonization_key}"))
                    continue

                jsonization_block = spec_impls[jsonization_key]
            else:
                jsonization_block = _generate_json_converter_for_class(cls=symbol)
        # TODO: uncomment once implemented
        # else:
        #     assert_never(symbol)
        #
        # assert jsonization_block is not None
        # jsonization_blocks.append(jsonization_block)

        # TODO: remove after debug
        if jsonization_block is not None:
            jsonization_blocks.append(jsonization_block)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        namespace {namespace}
        {{
        \tpublic static class Jsonization
        \t{{
        ''').replace('\t', csharp_common.INDENT))

    for i, jsonization_block in enumerate(jsonization_blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(
            textwrap.indent(jsonization_block, 2 * csharp_common.INDENT))

    writer.write(
        f"\n{csharp_common.INDENT}}}  // public static class Jsonization")
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
