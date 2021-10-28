"""Generate C# code for de/serialization based on the intermediate representation."""

import io
import textwrap
import xml.sax.saxutils
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Error, Stripped, Rstripped, Identifier
from aas_core_csharp_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming
)
from aas_core_csharp_codegen.csharp import specific_implementations


def _generate_enum_to_and_from_string(
        enumeration: intermediate.Enumeration
) -> Stripped:
    """Generate the methods for de/serializing enumeration from/to a string."""
    blocks = []  # type: List[Stripped]

    name = csharp_naming.enum_name(enumeration.name)

    # region To-string-map

    to_str_map_name = csharp_naming.private_property_name(
        Identifier(f"{enumeration.name}_to_string"))

    to_str_map_writer = io.StringIO()
    to_str_map_writer.write(
        f'private static readonly Dictionary<{name}, string> {to_str_map_name} = (\n'
        f'{csharp_common.INDENT}new Dictionary<{name}, string>()\n'
        f'{csharp_common.INDENT}{{\n')

    for i, literal in enumerate(enumeration.literals):
        literal_name = csharp_naming.enum_literal_name(literal.name)
        to_str_map_writer.write(
            f"{csharp_common.INDENT2}{{ {name}.{literal_name}, "
            f"{csharp_common.string_literal(literal.value)} }}")

        if i < len(enumeration.literals) - 1:
            to_str_map_writer.write(',')

        to_str_map_writer.write("\n")

    to_str_map_writer.write(f'{csharp_common.INDENT}}});')

    blocks.append(Stripped(to_str_map_writer.getvalue()))

    # endregion

    # region To-string-method

    to_str_name = csharp_naming.method_name(Identifier(f"to_string"))

    to_str_writer = io.StringIO()
    to_str_writer.write(
        textwrap.dedent(f'''\
            /// <summary>
            /// Retrieve the string representation of <paramref name="that" />.
            /// </summary>
            /// <remarks>
            /// If <paramref name="that" /> is not a valid literal, return <c>null</c>.
            /// </remarks>
            public string? {to_str_name}({name} that)
            {{
            \tstring value;
            \treturn {to_str_map_name}.TryGetValue(that, out value)
            \t\t? value
            \t\t: null;
            \t}}
            }}''').replace('\t', csharp_common.INDENT))

    blocks.append(Stripped(to_str_writer.getvalue()))

    # endregion

    # region From-string-map

    from_str_map_name = csharp_naming.private_property_name(
        Identifier(f"{enumeration.name}_from_string"))

    from_str_map_writer = io.StringIO()
    from_str_map_writer.write(
        f'private static readonly Dictionary<string, {name}> {from_str_map_name} = (\n'
        f'{csharp_common.INDENT}new Dictionary<string, {name}>()\n'
        f'{csharp_common.INDENT}{{\n')

    for i, literal in enumerate(enumeration.literals):
        literal_name = csharp_naming.enum_literal_name(literal.name)
        from_str_map_writer.write(
            f"{csharp_common.INDENT2}{{ {csharp_common.string_literal(literal.value)}, "
            f"{name}.{literal_name} }}")

        if i < len(enumeration.literals) - 1:
            from_str_map_writer.write(',')

        from_str_map_writer.write("\n")

    from_str_map_writer.write(f'{csharp_common.INDENT}}});')

    blocks.append(Stripped(from_str_map_writer.getvalue()))

    # endregion

    # region From-string-method

    from_str_name = csharp_naming.method_name(
        Identifier(f"{enumeration.name}_from_string"))

    from_str_writer = io.StringIO()
    from_str_writer.write(
        textwrap.dedent(f'''\
            /// <summary>
            /// Parse the string representation of <see cref={xml.sax.saxutils.quoteattr(name)} />.
            /// </summary>
            /// <remarks>
            /// If <paramref name="text" /> is not a valid string representation 
            /// of a literal of <see cref={xml.sax.saxutils.quoteattr(name)} />, 
            /// return <c>null</c>.
            /// </remarks>
            public string? {from_str_name}(string text)
            {{
            \t{name} value;
            \treturn {from_str_map_name}.TryGetValue(text, out value)
            \t\t? value
            \t\t: null;
            \t}}
            }}''').replace('\t', csharp_common.INDENT))

    blocks.append(Stripped(from_str_writer.getvalue()))

    # endregion

    return Stripped('\n\n'.join(blocks))


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
    blocks = [csharp_common.WARNING]  # type: List[Rstripped]

    using_directives = [
        "using System.Collections.Generic;  // can't alias"
    ]  # type: List[str]

    blocks.append(Stripped("\n".join(using_directives)))

    stringification_blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.Enumeration):
            continue

        stringification_blocks.append(
            _generate_enum_to_and_from_string(enumeration=symbol))

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        namespace {namespace}.Serialization
        {{
        \tpublic static class Stringification
        \t{{
        ''').replace('\t', csharp_common.INDENT))

    for i, stringification_block in enumerate(stringification_blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(
            textwrap.indent(stringification_block, 2 * csharp_common.INDENT))

    writer.write(
        f"\n{csharp_common.INDENT}}}  // public static class Stringification")
    writer.write(f"\n}}  // namespace {namespace}.Serialization")

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
