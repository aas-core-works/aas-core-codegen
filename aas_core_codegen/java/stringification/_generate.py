"""Generate Java code for de/serialization based on the intermediate representation."""

import io
import textwrap
import xml.sax.saxutils
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Error,
    Stripped,
    Identifier,
)
from aas_core_codegen.java import (
    common as java_common,
    naming as java_naming,
)
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
)


def _generate_enum_to_and_from_string(
    enumeration: intermediate.Enumeration,
) -> Stripped:
    """Generate the methods for de/serializing enumeration from/to a string."""
    blocks = []  # type: List[Stripped]

    name = java_naming.enum_name(enumeration.name)

    # region To-string-map

    to_str_map_name = java_naming.property_name(
        Identifier(f"{enumeration.name}_to_string")
    )

    to_str_map_writer = io.StringIO()
    to_str_map_writer.write(
        f"""\
private static final Map<{name}, String> {to_str_map_name} = Collections.unmodifiableMap(
{I}new HashMap<{name}, String>() {{{{
"""
    )

    for literal in enumeration.literals:
        literal_name = java_naming.enum_literal_name(literal.name)
        to_str_map_writer.write(
            f"{II}put({name}.{literal_name}, "
            f"{java_common.string_literal(literal.value)});"
        )

        to_str_map_writer.write("\n")

    to_str_map_writer.write(f"""{I}}}}});""")

    blocks.append(Stripped(to_str_map_writer.getvalue()))

    # endregion

    # region To-string-method

    to_str_name = java_naming.method_name(Identifier("to_string"))

    to_str_writer = io.StringIO()
    to_str_writer.write(
        f"""\
/**
 * Retrieve the string representation of {{@code that}}.
 *
 * <p>If {{@code that}} is not a valid literal, return {{@code Optional#empty()}}.
 */
public static Optional<String> {to_str_name}({name} that)
{{
{I}if (that == null) {{
{II}return Optional.<String>empty();
{I}}} else {{
{II}String value = {to_str_map_name}.get(that);
{II}if (value == null) {{
{III}return Optional.<String>empty();
{II}}} else {{
{III}return Optional.of({to_str_map_name}.get(value));
{II}}}
{I}}}
}}"""
    )

    blocks.append(Stripped(to_str_writer.getvalue()))

    # endregion

    # region From-string-map

    from_str_map_name = java_naming.private_property_name(
        Identifier(f"{enumeration.name}_from_string")
    )

    from_str_map_writer = io.StringIO()
    from_str_map_writer.write(
        f"""\
private static final Map<String, {name}> {from_str_map_name} = Collections.unmodifiableMap(
{I}new HashMap<String, {name}>() {{{{
"""
    )

    for literal in enumeration.literals:
        literal_name = java_naming.enum_literal_name(literal.name)
        from_str_map_writer.write(
            f"{II}put({java_common.string_literal(literal.value)}, "
            f"{name}.{literal_name});"
        )

        from_str_map_writer.write("\n")

    from_str_map_writer.write(f"{I}}}}});")

    blocks.append(Stripped(from_str_map_writer.getvalue()))

    # endregion

    # region From-string-method

    from_str_name = java_naming.method_name(
        Identifier(f"{enumeration.name}_from_string")
    )

    from_str_writer = io.StringIO()
    from_str_writer.write(
        f"""\
/**
 * Parse the string representation of {{@link {xml.sax.saxutils.quoteattr(name)}}}.
 *
 * <p>If {{@code text}} is not a valid string representation
 * of a literal of {{@link {xml.sax.saxutils.quoteattr(name)}}} />,
 * return {{@code Optional#empty()}}.
 */
public static Optional<{name}> {from_str_name}(String text)
{{
{I}{name} value = {from_str_name}.get(text);
{I}if (value == null) {{
{II}return Optional.<{name}>empty();
{I}}} else {{
{II}return Optional.of(value);
{I}}}
}}"""
    )

    blocks.append(Stripped(from_str_writer.getvalue()))

    # endregion

    return Stripped("\n\n".join(blocks))


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable, package: java_common.PackageIdentifier
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the Java code for the general serialization.

    The ``package`` defines the AAS Java package.
    """
    imports = [
        Stripped("import java.util.Collections;"),
        Stripped("import java.util.HashMap;"),
        Stripped("import java.util.Map;"),
        Stripped("import java.util.Optional;"),
        Stripped(f"import {package}.types.enums.*;"),
    ]  # type: List[Stripped]

    blocks = [
        java_common.WARNING,
        Stripped(f"package {package}.stringification;"),
        Stripped("\n".join(imports)),
    ]

    stringification_blocks = []  # type: List[Stripped]

    for enum in symbol_table.enumerations:
        stringification_blocks.append(
            _generate_enum_to_and_from_string(enumeration=enum)
        )

    writer = io.StringIO()
    writer.write(
        """\
public class Stringification {
"""
    )

    for i, stringification_block in enumerate(stringification_blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(stringification_block, II))

    writer.write(f"\n}}")

    blocks.append(Stripped(writer.getvalue()))

    blocks.append(java_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        assert not block.startswith("\n")
        assert not block.endswith("\n")
        out.write(block)

    out.write("\n")

    return out.getvalue(), None
