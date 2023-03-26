"""Generate Golang code for de/serialization of enumerations."""

import io
from typing import Tuple, Optional, List

from icontract import ensure

import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Error, Stripped, Identifier, indent_but_first_line
from aas_core_codegen.golang import (
    common as golang_common,
    naming as golang_naming,
)
from aas_core_codegen.golang.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


def _generate_model_type_from_string(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the function to translate our internal ``ModelType`` enum to string."""
    # NOTE (mristin, 2023-06-06):
    # Keep in sync with :func:`_generate_enum_from_string`. We copy/pasted and modified
    # the code as creating an enumeration object out of model type turned out to be
    # too tedious and *less* maintainable than copy/pasting. If you keep changing
    # this part of the code base a lot, and have trouble keeping this function in sync
    # with :func:`_generate_enum_from_string`, please consider re-factoring.

    blocks = []  # type: List[Stripped]

    # region From-string-map

    items = []  # type: List[str]
    for cls in symbol_table.concrete_classes:
        literal_name = golang_naming.enum_literal_name(
            Identifier("Model_type"), cls.name
        )

        literal_value = golang_common.string_literal(
            aas_core_codegen.naming.json_model_type(cls.name)
        )

        items.append(f"{literal_value}: aastypes.{literal_name}")

    from_str_map_name = golang_naming.private_constant_name(
        Identifier("model_type_from_string_map")
    )

    items_joined = "\n".join(f"{item}," for item in items)

    name = golang_naming.enum_name(Identifier("Model_type"))

    blocks.append(
        Stripped(
            f"""\
var {from_str_map_name} = map[string]aastypes.{name} {{
{I}{indent_but_first_line(items_joined, I)}
}}"""
        )
    )

    # endregion

    # region From-string-function
    from_str_name = golang_naming.function_name(Identifier("model_type_from_string"))

    blocks.append(
        Stripped(
            f"""\
// Parse `text` as a string representation of [aastypes.{name}].
//
// If not ok, the literal result is undefined.
func {from_str_name}(
{I}text string,
) (literal aastypes.{name}, ok bool) {{
{I}literal, ok = {from_str_map_name}[text]
{I}return
}}"""
        )
    )

    # endregion

    return Stripped("\n\n".join(blocks))


def _generate_model_type_to_string(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the function to translate a string to our internal ``ModelType``."""
    # NOTE (mristin, 2023-06-06):
    # Keep in sync with :func:`_generate_enum_to_string`. We copy/pasted and modified
    # the code as creating an enumeration object out of model type turned out to be
    # too tedious and *less* maintainable than copy/pasting. If you keep changing
    # this part of the code base a lot, and have trouble keeping this function in sync
    # with :func:`_generate_enum_to_string`, please consider re-factoring.

    blocks = []  # type: List[Stripped]

    # region To-string-map

    items = []  # type: List[str]
    for cls in symbol_table.concrete_classes:
        # NOTE (mristin, 2023-03-29):
        # We assume that enumeration literals are specified using ``iota``.

        literal_value = golang_common.string_literal(
            aas_core_codegen.naming.json_model_type(cls.name)
        )

        items.append(literal_value)

    to_str_array_name = golang_naming.private_constant_name(
        Identifier("model_type_to_string_array")
    )

    items_joined = "\n".join(f"{item}," for item in items)

    blocks.append(
        Stripped(
            f"""\
var {to_str_array_name} = [...]string {{
{I}{indent_but_first_line(items_joined, I)}
}}"""
        )
    )

    # endregion

    # region To-string-function

    to_str_name = golang_naming.function_name(Identifier("model_type_to_string"))

    name = golang_naming.enum_name(Identifier("Model_type"))

    blocks.append(
        Stripped(
            f"""\
// Translate `value` from [aastypes.{name}] to a string.
//
// If the value is not valid, the OK is false and the string representation is
// undefined.
func {to_str_name}(
{I}value aastypes.{name},
) (result string, ok bool) {{
{I}i := int(value)
{I}ok =
{II}i >= 0 &&
{II}i < len({to_str_array_name})

{I}if !ok {{
{II}return
{I}}}
{I}result = {to_str_array_name}[value]
{I}return
}}"""
        )
    )

    must_to_str_name = golang_naming.function_name(
        Identifier("must_model_type_to_string")
    )

    blocks.append(
        Stripped(
            f"""\
// Translate the `value` from [aastypes.{name}] to a string.
//
// Panic if the given value is invalid.
func {must_to_str_name}(
{I}value aastypes.{name},
) string {{
{I}result, ok := {to_str_name}(value)
{I}if !ok {{
{II}panic(
{III}fmt.Sprintf(
{IIII}"Invalid value of {name}: %v",
{IIII}value,
{III}),
{II})
{I}}}
{I}return result
}}"""
        )
    )

    # endregion

    return Stripped("\n\n".join(blocks))


def _generate_enum_from_string(enumeration: intermediate.Enumeration) -> Stripped:
    """Generate the functions for de-serializing enumeration from strings."""
    blocks = []  # type: List[Stripped]

    name = golang_naming.enum_name(enumeration.name)

    # region From-string-map

    items = []  # type: List[str]
    for literal in enumeration.literals:
        literal_name = golang_naming.enum_literal_name(enumeration.name, literal.name)
        literal_value = golang_common.string_literal(literal.value)

        items.append(f"{literal_value}: aastypes.{literal_name}")

    from_str_map_name = golang_naming.private_constant_name(
        Identifier(f"{enumeration.name}_from_string_map")
    )

    items_joined = "\n".join(f"{item}," for item in items)

    blocks.append(
        Stripped(
            f"""\
var {from_str_map_name} = map[string]aastypes.{name} {{
{I}{indent_but_first_line(items_joined, I)}
}}"""
        )
    )

    # endregion

    # region From-string-function
    from_str_name = golang_naming.function_name(
        Identifier(f"{enumeration.name}_from_string")
    )

    blocks.append(
        Stripped(
            f"""\
// Parse `text` as a string representation of [aastypes.{name}].
//
// If not ok, the literal result is undefined.
func {from_str_name}(
{I}text string,
) (literal aastypes.{name}, ok bool) {{
{I}literal, ok = {from_str_map_name}[text]
{I}return
}}"""
        )
    )

    # endregion

    return Stripped("\n\n".join(blocks))


def _generate_enum_to_string(enumeration: intermediate.Enumeration) -> Stripped:
    """Generate the functions for serializing enumerations to strings."""
    blocks = []  # type: List[Stripped]

    name = golang_naming.enum_name(enumeration.name)

    # region To-string-map

    items = []  # type: List[str]
    for literal in enumeration.literals:
        # NOTE (mristin, 2023-03-29):
        # We assume that enumeration literals are specified using ``iota``.
        literal_value = golang_common.string_literal(literal.value)

        items.append(literal_value)

    to_str_array_name = golang_naming.private_constant_name(
        Identifier(f"{enumeration.name}_to_string_array")
    )

    items_joined = "\n".join(f"{item}," for item in items)

    blocks.append(
        Stripped(
            f"""\
var {to_str_array_name} = [...]string {{
{I}{indent_but_first_line(items_joined, I)}
}}"""
        )
    )

    # endregion

    # region To-string-function

    to_str_name = golang_naming.function_name(
        Identifier(f"{enumeration.name}_to_string")
    )

    blocks.append(
        Stripped(
            f"""\
// Translate `value` from [aastypes.{name}] to a string.
//
// If the value is not valid, the OK is false and the string representation is
// undefined.
func {to_str_name}(
{I}value aastypes.{name},
) (result string, ok bool) {{
{I}i := int(value)
{I}ok =
{II}i >= 0 &&
{II}i < len({to_str_array_name})

{I}if !ok {{
{II}return
{I}}}
{I}result = {to_str_array_name}[value]
{I}return
}}"""
        )
    )

    must_to_str_name = golang_naming.function_name(
        Identifier(f"must_{enumeration.name}_to_string")
    )

    blocks.append(
        Stripped(
            f"""\
// Translate the `value` from [aastypes.{name}] to a string.
//
// Panic if the given value is invalid.
func {must_to_str_name}(
{I}value aastypes.{name},
) string {{
{I}result, ok := {to_str_name}(value)
{I}if !ok {{
{II}panic(
{III}fmt.Sprintf(
{IIII}"Invalid value of {name}: %v",
{IIII}value,
{III}),
{II})
{I}}}
{I}return result
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
    symbol_table: intermediate.SymbolTable, repo_url: Stripped
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the Golang code for the de/serialization of strings."""
    aastypes_url_literal = golang_common.string_literal(f"{repo_url}/types")

    blocks = [
        Stripped(
            """\
// Package stringification converts enumerations from and to string representations.
package stringification"""
        ),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{I}"fmt"
{I}aastypes {aastypes_url_literal}
)"""
        ),
        _generate_model_type_from_string(symbol_table=symbol_table),
        _generate_model_type_to_string(symbol_table=symbol_table),
    ]

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.Enumeration):
            continue

        blocks.append(_generate_enum_from_string(enumeration=our_type))
        blocks.append(_generate_enum_to_string(enumeration=our_type))

    blocks.append(golang_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue(), None
