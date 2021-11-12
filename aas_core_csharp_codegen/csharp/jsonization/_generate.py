"""Generate C# code for JSON-ization based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List, Sequence

from icontract import ensure

from aas_core_csharp_codegen import intermediate, naming, specific_implementations
from aas_core_csharp_codegen.common import Error, Stripped, Identifier, \
    assert_never, indent_but_first_line
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
        {I}Json.Serialization.JsonConverter<Aas.{enum_name}>
        {{
        {I}public override Aas.{enum_name} Read(
        {II}ref Json.Utf8JsonReader reader,
        {II}System.Type typeToConvert,
        {II}Json.JsonSerializerOptions options)
        {I}{{
        {II}if (reader.TokenType != Json.JsonTokenType.String)
        {II}{{
        {III}throw new Json.JsonException();
        {II}}}
        
        {II}string? text = reader.GetString();
        {II}if (text == null)
        {II}{{
        {III}throw new Json.JsonException();
        {II}}}
        
        {II}Aas.{enum_name}? value = Stringification.{enum_name}FromString(
        {III}text);
        {II}return value ?? throw new Json.JsonException(
        {III}$"Invalid {enum_name}: {{text}}");
        {I}}}
        
        {I}public override void Write(
        {II}Json.Utf8JsonWriter writer,
        {II}Aas.{enum_name} value,
        {II}Json.JsonSerializerOptions options)
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


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_read_for_interface(
        interface: intermediate.Interface,
        implementers: Sequence[intermediate.Class]
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the ``Read`` method for de-serializing the ``interface``."""
    # NOTE (mristin, 2021-11-03):
    # Since we perform an on-demand de-serialization, we do not know the discriminating
    # model type (*i.e.*, the concrete class of the object). Hence we need to
    # de-serialize the union of all the possible properties. Once we are done
    # de-serializing all the properties, we will call the appropriate constructor.

    property_union, error = intermediate.make_union_of_properties(
        interface=interface, implementers=implementers)
    if error is not None:
        return None, error

    assert property_union is not None

    blocks = [
        Stripped(textwrap.dedent(f'''\
            if (reader.TokenType != Json.JsonTokenType.StartObject)
            {{
            {I}throw new Json.JsonException();
            }}''')),
        Stripped('string? modelType = null;')
    ]

    # region Initializations

    if len(property_union) > 0:
        initialization_lines = [
            Stripped('// Prefix the property variables with "the" to avoid conflicts')
        ]  # type: List[Stripped]

        for prop_name in sorted(property_union.keys()):
            type_anno = property_union[prop_name]

            var_name = csharp_naming.variable_name(Identifier(f'the_{prop_name}'))
            prop_type = csharp_common.generate_type(type_anno)

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
    return_writer.write(textwrap.dedent('''\
        switch (modelType)
        {
        '''))

    for implementer in implementers:
        constructor_arg_names = [arg.name for arg in implementer.constructor.arguments]

        cls_name = csharp_naming.class_name(implementer.name)
        json_model_type = naming.json_model_type(implementer.name)

        if len(constructor_arg_names) == 0:
            return_writer.write(textwrap.indent(textwrap.dedent(f'''\
                case {csharp_common.string_literal(json_model_type)}:
                {I}return new Aas.{cls_name}();'''), I))
        else:
            return_writer.write(textwrap.indent(textwrap.dedent(f'''\
                case {csharp_common.string_literal(json_model_type)}:
                {I}return new Aas.{cls_name}(\n'''), I))

            for i, constructor_arg_name in enumerate(constructor_arg_names):
                prop_name = constructor_arg_name
                var_name = csharp_naming.variable_name(
                    Identifier(f'the_{prop_name}'))

                prop_type = property_union[prop_name]

                if not isinstance(
                        prop_type, intermediate.OptionalTypeAnnotation):
                    json_prop_name = naming.json_property(prop_name)

                    error_msg = csharp_common.string_literal(
                        f'Required property is missing: {json_prop_name}')

                    return_writer.write(textwrap.indent(textwrap.dedent(f'''\
                        {var_name} ?? throw new Json.JsonException(
                        {I}{error_msg})'''), III))
                else:
                    return_writer.write(f'{III}{var_name}')

                if i < len(constructor_arg_names) - 1:
                    return_writer.write(',\n')
                else:
                    return_writer.write(');\n')

    return_writer.write(textwrap.indent(textwrap.dedent(f'''\
        default:
        {I}throw new Json.JsonException(
        {II}$"Unknown model type: {{modelType}}");
        '''), I))

    return_writer.write('\n}  // switch on modelType')

    # endregion

    # region Loop and switch

    token_case_blocks = [
        Stripped(f'''\
case Json.JsonTokenType.EndObject:
{I}{indent_but_first_line(return_writer.getvalue(), I)}''')]

    property_switch_writer = io.StringIO()
    property_switch_writer.write(textwrap.dedent(f'''\
        string propertyName = reader.GetString()
        {I}?? throw new System.InvalidOperationException(
        {II}"Unexpected property name null");

        switch (propertyName)
        {{
        '''))

    for prop_name in sorted(property_union.keys()):
        type_anno = property_union[prop_name]

        var_name = csharp_naming.variable_name(Identifier(f'the_{prop_name}'))

        if isinstance(type_anno, intermediate.OptionalTypeAnnotation):
            prop_type = csharp_common.generate_type(type_anno.value)
        else:
            prop_type = csharp_common.generate_type(type_anno)

        json_prop_name = naming.json_property(prop_name)

        property_switch_writer.write(textwrap.indent(textwrap.dedent(f'''\
            case {csharp_common.string_literal(json_prop_name)}: 
            {I}{var_name} =  (
            {II}Json.JsonSerializer.Deserialize<{prop_type}>(
            {III}ref reader));
            {I}break;
            '''), I))

    property_switch_writer.write(textwrap.indent(textwrap.dedent(f'''\
        case "modelType":
        {I}modelType = Json.JsonSerializer.Deserialize<string>(
        {II}ref reader);
        {I}break;
        '''), I))

    interface_name = csharp_naming.interface_name(interface.name)

    property_switch_writer.write(textwrap.dedent(f'''\
        {I}default:
        {II}throw new Json.JsonException(
        {III}$"Unexpected property in an implementer class " + 
        {III}$"of {interface_name}: {{propertyName}}");
        }}  // switch on propertyName'''))

    token_case_blocks.append(Stripped(f'''\
case Json.JsonTokenType.PropertyName:
{I}{indent_but_first_line(property_switch_writer.getvalue(), I)}
{I}break;'''))

    token_case_blocks.append(Stripped(textwrap.dedent(f'''\
        default:
        {I}throw new Json.JsonException();''')))

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

        while_writer.write(textwrap.indent(token_case_block, II))

    while_writer.write(
        f'\n'
        f'{I}}}  // switch on token type\n'
        f'}}  // while reader.Read')

    blocks.append(Stripped(while_writer.getvalue()))

    blocks.append(Stripped('throw new Json.JsonException();'))

    # endregion

    # region Bundle it all together

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public override Aas.{interface_name} Read(
        {I}ref Json.Utf8JsonReader reader,
        {I}System.Type typeToConvert,
        {I}Json.JsonSerializerOptions options)
        {{
        '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')
        writer.write(textwrap.indent(block, I))

    writer.write('\n}')

    # endregion

    return Stripped(writer.getvalue()), None


def _generate_write_for_interface(
    interface: intermediate.Interface,
    implementers: Sequence[intermediate.Class]
) -> Stripped:
    """Generate the ``Write`` method for serializing the ``interface``."""
    interface_name = csharp_naming.interface_name(interface.name)

    # region Switch on implementer type

    switch_writer = io.StringIO()
    switch_writer.write(textwrap.dedent('''\
        switch (that)
        {
        '''))

    for implementer in implementers:
        cls_name = csharp_naming.class_name(implementer.name)
        var_name = csharp_naming.variable_name(Identifier(f'the_{implementer.name}'))

        switch_writer.write(textwrap.indent(textwrap.dedent(f'''\
            case {cls_name} {var_name}:
            {I}Json.JsonSerializer.Serialize(
            {II}writer, {var_name});
            {I}break;
            '''), I))

    switch_writer.write(textwrap.indent(textwrap.dedent(f'''\
        default:
        {I}throw new System.ArgumentException(
            $"Instance `that` of type {{that.GetType()}} is " + 
            $"not an implementer class of {interface_name}: {{that}}");'''), I))

    switch_writer.write('\n}')

    # endregion

    # region Bundle it all together

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public override void Write(
        {I}Json.Utf8JsonWriter writer,
        {I}Aas.{interface_name} that,
        {I}Json.JsonSerializerOptions options)
        {{
        '''))

    writer.write(switch_writer.getvalue())

    writer.write('\n}')

    # endregion

    return Stripped(writer.getvalue())


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_json_converter_for_interface(
        interface: intermediate.Interface,
        implementers: Sequence[intermediate.Class]
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the custom JSON converter based on the intermediate ``interface``."""
    read_code, error = _generate_read_for_interface(
        interface=interface, implementers=implementers)

    if error is not None:
        return None, error

    write_code = _generate_write_for_interface(
        interface=interface, implementers=implementers)

    interface_name = csharp_naming.interface_name(interface.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public class {interface_name}JsonConverter :
        {I}Json.Serialization.JsonConverter<Aas.{interface_name}>
        {{
        {I}public override bool CanConvert(System.Type typeToConvert)
        {I}{{
        {II}return typeof(Aas.{interface_name}).IsAssignableFrom(typeToConvert);
        {I}}}'''))

    writer.write('\n\n')

    writer.write(textwrap.indent(read_code, I))

    writer.write('\n\n')

    writer.write(textwrap.indent(write_code, I))

    writer.write(f'\n}}  // {interface_name}JsonConverter')

    return Stripped(writer.getvalue()), None


def _generate_read_for_class(
        cls: intermediate.Class
) -> Stripped:
    """Generate the ``Read`` method for de-serializing the class ``cls``."""
    blocks = [
        Stripped(textwrap.dedent(f'''\
            if (reader.TokenType != Json.JsonTokenType.StartObject)
            {{
            {I}throw new Json.JsonException();
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

    cls_name = csharp_naming.class_name(cls.name)

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
                json_prop_name = naming.json_property(prop.name)

                error_msg = csharp_common.string_literal(
                    f'Required property is missing: {json_prop_name}')

                return_writer.write(textwrap.indent(textwrap.dedent(f'''\
                    {var_name} ?? throw new Json.JsonException(
                    {I}{error_msg})'''), I))
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
case Json.JsonTokenType.EndObject:
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
                {II}Json.JsonSerializer.Deserialize<{prop_type}>(
                {III}ref reader));
                {I}break;
                '''), I))

        if cls.json_serialization.with_model_type:
            property_switch_writer.write(textwrap.indent(textwrap.dedent(f'''\
                case "modelType": 
                {I}// Ignore the property modelType as we already know the exact type
                {I}break;
                '''), I))

        property_switch_writer.write(textwrap.dedent(f'''\
            {I}default:
            {II}// Ignore an unknown property
            {II}if (!reader.Read())
            {II}{{
            {III}throw new Json.JsonException(
            {IIII}$"Unexpected end-of-stream after the property: {{propertyName}}");
            {II}}}
            {II}if (!reader.TrySkip())
            {II}{{
            {III}throw new Json.JsonException(
            {IIII}"Unexpected end-of-stream when skipping " + 
            {IIII}$"the value of the unknown property: {{propertyName}}");
            {II}}}
            {II}break;
            }}  // switch on propertyName'''))

        token_case_blocks.append(Stripped(f'''\
case Json.JsonTokenType.PropertyName:
{I}{indent_but_first_line(property_switch_writer.getvalue(), I)}
{I}break;'''))

    token_case_blocks.append(Stripped(textwrap.dedent(f'''\
        default:
        {I}throw new Json.JsonException();''')))

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

        while_writer.write(textwrap.indent(token_case_block, II))

    while_writer.write(
        f'\n'
        f'{I}}}  // switch on token type\n'
        f'}}  // while reader.Read')

    blocks.append(Stripped(while_writer.getvalue()))

    blocks.append(Stripped('throw new Json.JsonException();'))

    # endregion

    # region Bundle it all together

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public override Aas.{cls_name} Read(
        {I}ref Json.Utf8JsonReader reader,
        {I}System.Type typeToConvert,
        {I}Json.JsonSerializerOptions options)
        {{
        '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')
        writer.write(textwrap.indent(block, I))

    writer.write('\n}')

    # endregion

    return Stripped(writer.getvalue())


def _generate_write_for_class(
        cls: intermediate.Class
) -> Stripped:
    """Generate the ``Write`` method for serializing the class ``cls``."""
    blocks = [Stripped('writer.WriteStartObject();')]

    if cls.json_serialization.with_model_type:
        json_model_type = naming.json_model_type(cls.name)
        blocks.append(Stripped(textwrap.dedent(f'''\
            writer.WritePropertyName("modelType");
            Json.JsonSerializer.Serialize(
            {I}writer, {csharp_common.string_literal(json_model_type)});''')))

    for prop in cls.properties:
        prop_name = csharp_naming.property_name(prop.name)
        json_prop_name = naming.json_property(prop.name)

        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            blocks.append(Stripped(textwrap.dedent(f'''\
                writer.WritePropertyName({csharp_common.string_literal(json_prop_name)});
                Json.JsonSerializer.Serialize(
                {I}writer, that.{prop_name});''')))
        else:
            blocks.append(Stripped(textwrap.dedent(f'''\
                if (that.{prop_name} != null)
                {{
                {I}writer.WritePropertyName({csharp_common.string_literal(json_prop_name)});
                {I}Json.JsonSerializer.Serialize(
                {II}writer, that.{prop_name});
                }}''')))

    blocks.append(Stripped('writer.WriteEndObject();'))

    # region Bundle it all together

    cls_name = csharp_naming.class_name(cls.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public override void Write(
        {I}Json.Utf8JsonWriter writer,
        {I}Aas.{cls_name} that,
        {I}Json.JsonSerializerOptions options)
        {{
        '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')
        writer.write(textwrap.indent(block, I))

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
        {I}Json.Serialization.JsonConverter<Aas.{cls_name}>
        {{
        '''))

    writer.write(textwrap.indent(_generate_read_for_class(cls=cls), I))

    writer.write('\n\n')

    writer.write(textwrap.indent(_generate_write_for_class(cls=cls), I))

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
            using Json = System.Text.Json;
            using System.Collections.Generic;  // can't alias

            using Aas = {namespace};"""))
    ]

    jsonization_blocks = []  # type: List[Stripped]
    converters = []  # type: List[Identifier]

    for symbol in symbol_table.symbols:
        jsonization_block = None  # type: Optional[Stripped]
        if isinstance(symbol, intermediate.Enumeration):
            jsonization_block = _generate_json_converter_for_enumeration(
                enumeration=symbol)

            converters.append(Identifier(
                f'{csharp_naming.enum_name(symbol.name)}JsonConverter'))
        elif isinstance(symbol, intermediate.Interface):
            # Only interfaces with ``modelType`` property can be deserialized as
            # otherwise we would lack the discriminating property.
            if not symbol.json_serialization.with_model_type:
                continue

            implementers = interface_implementers[symbol]
            jsonization_block, error = _generate_json_converter_for_interface(
                interface=symbol,
                implementers=implementers)

            if error is not None:
                errors.append(error)
                continue

            converters.append(Identifier(
                f'{csharp_naming.interface_name(symbol.name)}JsonConverter'))

        elif isinstance(symbol, intermediate.Class):
            if symbol.is_implementation_specific:
                jsonization_key = specific_implementations.ImplementationKey(
                    f'Jsonization/{symbol.name}_json_converter.cs')

                implementation = spec_impls.get(jsonization_key, None)
                if implementation is None:
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

            converters.append(Identifier(
                f'{csharp_naming.class_name(symbol.name)}JsonConverter'))
        else:
            assert_never(symbol)

        assert jsonization_block is not None
        jsonization_blocks.append(jsonization_block)

    if len(converters) == 0:
        jsonization_blocks.append(Stripped(textwrap.dedent(f'''\
            public static List<Json.JsonConverter> JsonConverters()
            {{
            {I}return new List<Json.JsonConverter>();
            }}''')))
    else:
        converters_writer = io.StringIO()
        converters_writer.write(textwrap.dedent(f'''\
            /// <summary>
            /// Create and populate a list of our custom-tailored JSON converters.
            /// </summary>
            public static List<Json.Serialization.JsonConverter> CreateJsonConverters()
            {{
            {I}return new List<Json.Serialization.JsonConverter>()
            {I}{{
            '''))

        for i, converter in enumerate(converters):
            converters_writer.write(f'{II}new {converter}()')

            if i < len(converters) - 1:
                converters_writer.write(',')

            converters_writer.write('\n')

        converters_writer.write(f'{I}}};\n}}')
        jsonization_blocks.append(Stripped(converters_writer.getvalue()))

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    # TODO (mristin, 2021-11-06): add a good docstring 🠒 add examples!
    writer.write(textwrap.dedent(f'''\
        namespace {namespace}
        {{
        {I}public static class Jsonization
        {I}{{
        '''))

    for i, jsonization_block in enumerate(jsonization_blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(jsonization_block, II))

    writer.write(
        f"\n{I}}}  // public static class Jsonization")
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
