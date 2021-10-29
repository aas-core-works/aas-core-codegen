"""Generate C# code for JSON-ization based on the intermediate representation."""

import io
import textwrap
import xml.sax.saxutils
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_csharp_codegen import intermediate, naming
from aas_core_csharp_codegen.common import Error, Stripped, Identifier, assert_never
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
        {II}if (value == null)
        {II}{{
        {III}throw new System.Text.Json.JsonException(
        {IIII}$"Invalid {enum_name}: {{text}}");
        {II}}}
        {II}return value;
        {I}}}
        
        {I}public override void Write(
        {II}Utf8JsonWriter writer,
        {II}Aas.{enum_name} value,
        {II}System.Text.Json.JsonSerializerOptions options)
        {I}{{
        {II}string? text = Stringification.{enum_name}ToString(
        {III}value);
        {II}if (text == null)
        {II}{{
        {III}throw new InvalidArgumentException(
        {IIII}$"Invalid {enum_name}: {{value}}");
        {II}}}
        
        {II}writer.WriteStringValue(text);
        {I}}}
        }}'''))


def _generate_json_converter_for_interface(
        interface: intermediate.Interface
) -> Stripped:
    """Generate the custom JSON converter based on the intermediate ``interface``."""
    # TODO: implement
    raise NotImplementedError()


def _generate_read_for_class(
        cls: intermediate.Class
) -> Stripped:
    """Generate the body of the ``Read`` method for deserializing a class ``cls``."""
    cls_name = csharp_naming.class_name(cls.name)

    blocks = []  # type: List[Stripped]

    # TODO: continue here
    #  * initialize all the variables to null
    #  * map property names to lambda setters
    #  * switch on property names 🠒 execute the setters, throw if the property is not known.
    #  * check for missing required fields
    #  * construct
    for prop in cls.properties:
        var_name = csharp_naming.variable_name(prop.name)
        prop_type = csharp_common.generate_type(prop.type_annotation)
        prop_name = naming.json_property(prop.name)

        blocks.append(Stripped(textwrap.dedent(f'''\
            if (reader.TokenType != System.Text.Json.JsonTokenType.StartObject)
            {{
            {I}throw new JsonException();
            }}''')))
        #
        #     // Don't pass in options when recursively calling Deserialize.
        #     {prop_type} {var_name} = (
        #     {I}System.Text.Json.JsonSerializer.Deserialize<{prop_type}>(
        #     {II}ref reader));''')))
        #
        # if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        #     blocks.append(Stripped(textwrap.dedent(f'''\
        #         if ({var_name} == null)
        #         {{
        #         {I}throw new System.Text.Json.JsonException(
        #         {II}"Required property is missing: {prop_name}");
        #         }}''')))

    constructor_call_writer = io.StringIO()
    constructor_call_writer.write(f'return new Aas.{cls_name}(\n')

    for i, prop in enumerate(cls.properties):
        var_name = csharp_naming.variable_name(prop.name)
        constructor_call_writer.write(f'{I}{var_name}')

        if i < len(cls.properties) - 1:
            constructor_call_writer.write(',\n')
        else:
            constructor_call_writer.write(');')

    blocks.append(Stripped(constructor_call_writer.getvalue()))

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

    # TODO: implement Write

    writer.write('\n}')

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
        namespace: csharp_common.NamespaceIdentifier
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code for the general serialization.

    The ``namespace`` defines the AAS C# namespace.
    """
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
            using InvalidArgumentException = System.InvalidArgumentException;
            using System.Collections.Generic;  // can't alias

            using Aas = {namespace};"""))
    ]

    jsonization_blocks = []  # type: List[Stripped]

    # TODO: idea how to avoid modelType:
    #  * for each interface, collect all the implementer classes
    #  * these classes have model_typed = True, others have False
    #  * when serializing, add modelType property

    # TODO: for interface
    #  * collect all the implementers
    #  * collect the union of their properties
    #  🠒 make sure no duplicates!
    #  🠒 make sure all the type annotations are equal!
    #  * if more than one implementer: include modelType
    #  * initialize all the properties (including modelType) to null
    #  * deserialize by switching 🠒 similar as for the classes
    #  * switch on modelType 🠒 check for required fields! return the constructor

    for symbol in symbol_table.symbols:
        jsonization_block = None  # type: Optional[Stripped]
        if isinstance(symbol, intermediate.Enumeration):
            jsonization_block = _generate_json_converter_for_enumeration(
                enumeration=symbol)
        # TODO: uncomment once implemented
        # elif isinstance(symbol, intermediate.Interface):
        #     jsonization_block = _generate_json_converter_for_interface(
        #         interface=symbol)
        elif isinstance(symbol, intermediate.Class):
            jsonization_block = _generate_json_converter_for_class(
                cls=symbol)
        # else:
        #     assert_never(symbol)
        #
        # assert jsonization_block is not None
        # jsonization_blocks.append(jsonization_block)

        # TODO: remove after debug
        if jsonization_block is not None:
            jsonization_blocks.append(jsonization_block)

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
