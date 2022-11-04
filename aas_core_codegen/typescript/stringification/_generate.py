"""Generate TypeScript code for de/serialization of enumerations."""

import io
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import Error, Stripped, Identifier, indent_but_first_line
from aas_core_codegen.typescript import (
    common as typescript_common,
    naming as typescript_naming,
)
from aas_core_codegen.typescript.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
)


def _generate_enum_from_string(enumeration: intermediate.Enumeration) -> Stripped:
    """Generate the functions for de-serializing enumeration from strings."""
    blocks = []  # type: List[Stripped]

    name = typescript_naming.enum_name(enumeration.name)

    # region From-string-map

    items = []  # type: List[str]
    for literal in enumeration.literals:
        literal_name = typescript_naming.enum_literal_name(literal.name)
        literal_value = typescript_common.string_literal(literal.value)

        items.append(f"[{literal_value}, AasTypes.{name}.{literal_name}]")

    from_str_map_name = typescript_naming.constant_name(
        Identifier(f"{enumeration.name}_from_string")
    )

    items_joined = ",\n".join(items)

    blocks.append(
        Stripped(
            f"""\
const {from_str_map_name} = new Map<string, AasTypes.{name}>([
{I}{indent_but_first_line(items_joined, I)}
]);"""
        )
    )

    # endregion

    # region From-string-function

    from_str_name = typescript_naming.function_name(
        Identifier(f"{enumeration.name}_from_string")
    )

    blocks.append(
        Stripped(
            f"""\
/**
 * Parse `text` as a string representation of {{@link types!{name}}}.
 *
 * @param text - string representation of {{@link types!{name}}}
 * @returns literal of {{@link types!{name}}}, if valid, and `null` otherwise
 */
export function {from_str_name}(
{I}text: string
): AasTypes.{name} | null {{
{I}const result = {from_str_map_name}.get(text);
{I}return result !== undefined ? result : null;
}}"""
        )
    )

    # endregion

    return Stripped("\n\n".join(blocks))


def _generate_enum_to_string(enumeration: intermediate.Enumeration) -> Stripped:
    """Generate the functions for serializing enumerations to strings."""
    blocks = []  # type: List[Stripped]

    name = typescript_naming.enum_name(enumeration.name)

    # region To-string-map

    items = []  # type: List[str]
    for literal in enumeration.literals:
        literal_name = typescript_naming.enum_literal_name(literal.name)
        literal_value = typescript_common.string_literal(literal.value)

        items.append(f"[AasTypes.{name}.{literal_name}, {literal_value}]")

    to_str_map_name = typescript_naming.constant_name(
        Identifier(f"{enumeration.name}_to_string")
    )

    items_joined = ",\n".join(items)

    blocks.append(
        Stripped(
            f"""\
const {to_str_map_name} = new Map<AasTypes.{name}, string>([
{I}{indent_but_first_line(items_joined, I)}
]);"""
        )
    )

    # endregion

    # region To-string-function

    to_str_name = typescript_naming.function_name(
        Identifier(f"{enumeration.name}_to_string")
    )

    blocks.append(
        Stripped(
            f"""\
/**
 * Translate {{@link types!{name}}} to a string.
 *
 * @param value - to be stringified
 * @returns string representation of {{@link types!{name}}}, if `value` valid, and `null` otherwise
 */
export function {to_str_name}(
{I}value: AasTypes.{name}
): string | null {{
{I}const result = {to_str_map_name}.get(value);
{I}return result !== undefined ? result : null;
}}"""
        )
    )

    must_to_str_name = typescript_naming.function_name(
        Identifier(f"must_{enumeration.name}_to_string")
    )

    blocks.append(
        Stripped(
            f"""\
/**
 * Translate {{@link types!{name}}} to a string.
 *
 * @param value - to be stringified
 * @returns string representation of {{@link types!{name}}}
 * @throws
 * {{@link https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error|Error}}
 * if the `value` is invalid
 */
export function {must_to_str_name}(
{I}value: AasTypes.{name}
): string {{
{I}const result = {to_str_map_name}.get(value);
{I}if (result === undefined) {{
{II}throw new Error(
{III}`Invalid literal of {name}: ${{value}}`
{II});
{I}}}
{I}return result;
}}"""
        )
    )

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
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the TypeScript code for the de/serialization of strings."""
    blocks = [
        Stripped(
            """\
/**
 * De/serialize enumerations from and to string representations.
 */"""
        ),
        typescript_common.WARNING,
        Stripped('import * as AasTypes from "./types";'),
    ]

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.Enumeration):
            continue

        blocks.append(_generate_enum_from_string(enumeration=our_type))
        blocks.append(_generate_enum_to_string(enumeration=our_type))

    blocks.append(typescript_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue(), None
