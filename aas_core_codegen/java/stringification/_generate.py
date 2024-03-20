"""Generate Java code for de/serialization based on the intermediate representation."""

import io
import textwrap
import xml.sax.saxutils
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    indent_but_first_line,
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

    enum_to_string_blocks = []  # type: List[Stripped]

    for literal in enumeration.literals:
        literal_name = java_naming.enum_literal_name(literal.name)

        literal_string = java_common.string_literal(literal.value)

        enum_to_string_blocks.append(
            Stripped(f"""temp.put({name}.{literal_name}, {literal_string});""")
        )

    enum_to_string_mapping = "\n".join(enum_to_string_blocks)

    to_str_map_name = java_naming.property_name(
        Identifier(f"{enumeration.name}_to_string")
    )

    to_str_map = Stripped(
        f"""\
private static final Map<{name}, String> {to_str_map_name};
static {{
{I}final Map<{name}, String> temp = new HashMap<>();

{I}{indent_but_first_line(enum_to_string_mapping, I)}

{I}if (!temp.keySet().containsAll(Arrays.asList({name}.values()))) {{
{II}throw new IllegalStateException("Unmapped {name}");
{I}}}

{I}{to_str_map_name} = Collections.unmodifiableMap(temp);
}}"""
    )

    blocks.append(to_str_map)

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
{I}return Optional.ofNullable(that).map({to_str_map_name}::get);
}}"""
    )

    blocks.append(Stripped(to_str_writer.getvalue()))

    # endregion

    # region From-string-map

    string_to_enum_blocks = []  # type: List[Stripped]

    for literal in enumeration.literals:
        literal_name = java_naming.enum_literal_name(literal.name)

        literal_string = java_common.string_literal(literal.value)

        string_to_enum_blocks.append(
            Stripped(f"""temp.put({literal_string}, {name}.{literal_name});""")
        )

    string_to_enum_mapping = "\n".join(string_to_enum_blocks)

    from_str_map_name = java_naming.private_property_name(
        Identifier(f"{enumeration.name}_from_string")
    )

    from_str_map = Stripped(
        f"""\
private static final Map<String, {name}> {from_str_map_name};
static {{
{I}final Map<String, {name}> temp = new HashMap<>();

{I}{indent_but_first_line(string_to_enum_mapping, I)}

{I}if (!temp.values().containsAll(Arrays.asList({name}.values()))) {{
{II}throw new IllegalStateException("Unmapped {name}");
{I}}}

{I}{from_str_map_name} = Collections.unmodifiableMap(temp);
}}"""
    )

    blocks.append(from_str_map)

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
 * of a literal of {{@link {xml.sax.saxutils.quoteattr(name)}}},
 * return {{@code Optional#empty()}}.
 */
public static Optional<{name}> {from_str_name}(String text)
{{
{I}{name} value = {from_str_name}.get(text);
{I}if (value == null) {{
{II}return Optional.empty();
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

    The ``package`` defines the root Java package.
    """
    stringification_blocks = []  # type: List[Stripped]

    for enum in symbol_table.enumerations:
        stringification_blocks.append(
            _generate_enum_to_and_from_string(enumeration=enum)
        )

    stringification_code = Stripped("\n\n".join(stringification_blocks))

    code = Stripped(
        f"""\
{java_common.WARNING}

package {package}.stringification;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import {package}.types.enums.*;

public class Stringification {{
{I}{indent_but_first_line(stringification_code, I)}
}}

{java_common.WARNING}"""
    )

    return f"{code}\n", None
