"""Generate the test code for the JSON de/serialization of enums."""

import io
from typing import List

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import Stripped, Identifier
from aas_core_codegen.typescript import (
    common as typescript_common,
    naming as typescript_naming,
)
from aas_core_codegen.typescript.common import (
    INDENT as I,
    INDENT2 as II,
)


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable) -> str:
    """Generate the test code for the JSON de/serialization of enums."""
    blocks = [
        Stripped(
            """\
/**
 * Test JSON de/serialization of enumeration literals.
 */"""
        ),
        typescript_common.WARNING,
        Stripped(
            """\
import * as AasJsonization from "../src/jsonization";
import * as AasTypes from "../src/types";"""
        ),
    ]  # type: List[Stripped]

    for enumeration in symbol_table.enumerations:
        enum_name_typescript = typescript_naming.enum_name(enumeration.name)

        assert (
            len(enumeration.literals) > 0
        ), f"Unexpected enumeration without literals: {enumeration.name}"

        literal = enumeration.literals[0]
        literal_name_typescript = typescript_naming.enum_literal_name(literal.name)

        deserialization_function = typescript_naming.function_name(
            Identifier(f"{enumeration.name}_from_jsonable")
        )

        blocks.append(
            Stripped(
                f"""\
test("{enum_name_typescript} round-trip OK", () => {{
{I}const jsonable = {typescript_common.string_literal(literal.value)};

{I}const literalOrError = AasJsonization.{deserialization_function}(
{II}jsonable
{I});

{I}expect(literalOrError.error).toBeNull();
{I}const literal = literalOrError.mustValue();

{I}expect(literal).toStrictEqual(
{II}AasTypes.{enum_name_typescript}.{literal_name_typescript}
{I});
}});"""
            )
        )

        literal_value_set = set(literal.value for literal in enumeration.literals)
        invalid_literal_value = "invalid-literal"
        while invalid_literal_value in literal_value_set:
            invalid_literal_value = f"very-{invalid_literal_value}"

        expected_message = (
            f"Not a valid string representation of a literal "
            f"of {enum_name_typescript}: {invalid_literal_value}"
        )

        blocks.append(
            Stripped(
                f"""\
test("{enum_name_typescript} deserialization fail", () => {{
{I}const jsonable = {typescript_common.string_literal(invalid_literal_value)};

{I}const literalOrError = AasJsonization.{deserialization_function}(
{II}jsonable
{I});

{I}expect(literalOrError.error.message).toStrictEqual(
{II}{typescript_common.string_literal(expected_message)}
{I});
}});"""
            )
        )

    blocks.append(typescript_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
