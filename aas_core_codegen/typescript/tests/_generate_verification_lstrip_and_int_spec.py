"""Generate the unit tests for ``str.lstrip`` and ``int`` on strings."""

import io
from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped
from aas_core_codegen.intermediate import uses as intermediate_uses
from aas_core_codegen.typescript import common as typescript_common
from aas_core_codegen.typescript.common import INDENT as I, INDENT2 as II


# fmt: off
@require(
    lambda symbol_table:
    intermediate_uses.lstrip_call(symbol_table) or intermediate_uses.int_call(symbol_table)
)
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable) -> str:
    """
    Generate the unit tests for ``str.lstrip`` and ``int`` on strings.

    The transpiled ``str.lstrip`` follows the Python semantics, and the transpiled
    ``int`` is stricter than the Python one so that all the SDKs behave the same.
    All the SDKs test against the very same cases, see
    :py:mod:`aas_core_codegen.tests_common`.
    """
    blocks = [
        Stripped(
            """\
/**
 * Test `lstrip` and `int` on strings as used in the transpiled code.
 *
 * @remarks
 *
 * The transpiled `lstrip` follows the Python implementation, since Python is
 * the language of the meta-model specifications. Hence, it strips
 * the characters (code points) rather than the UTF-16 code units.
 *
 * The built-in `int` is transpiled to `AasCommon.parseSafeInt`, which is
 * stricter than the Python `int`. It accepts only an optional sign followed by
 * the ASCII digits, and only the safe integers, *i.e.*, the integers within
 * `Number.MIN_SAFE_INTEGER` and `Number.MAX_SAFE_INTEGER`. Otherwise, it throws.
 *
 * All the SDKs test against the very same cases.
 */"""
        ),
        typescript_common.WARNING,
    ]  # type: List[Stripped]

    blocks.append(Stripped('import * as AasCommon from "../src/common";'))

    if intermediate_uses.lstrip_call(symbol_table):
        for text, chars, expected in tests_common.LSTRIP_CASES:
            title = typescript_common.string_literal(
                f"{text!r}.lstrip({chars!r}) gives {expected!r}"
            )

            text_literal = typescript_common.string_literal(text)
            chars_literal = typescript_common.string_literal(chars)
            expected_literal = typescript_common.string_literal(expected)

            blocks.append(
                Stripped(
                    f"""\
test({title}, () => {{
{I}expect(AasCommon.lstrip({text_literal}, {chars_literal})).toStrictEqual(
{II}{expected_literal}
{I});
}});"""
                )
            )

    if intermediate_uses.int_call(symbol_table):
        for text, expected_int in tests_common.PARSE_INT_CASES:
            title = typescript_common.string_literal(
                f"int({text!r}) gives {expected_int}"
            )

            text_literal = typescript_common.string_literal(text)
            expected_literal = typescript_common.numeric_literal(expected_int)

            # NOTE (mristin):
            # We compare the results with ``toBe``, which uses ``Object.is``, so
            # that we also make sure that we never return a negative zero.
            blocks.append(
                Stripped(
                    f"""\
test({title}, () => {{
{I}expect(AasCommon.parseSafeInt({text_literal})).toBe(
{II}{expected_literal}
{I});
}});"""
                )
            )

        for text in tests_common.PARSE_INT_INVALID_CASES:
            title = typescript_common.string_literal(f"int({text!r}) throws")

            text_literal = typescript_common.string_literal(text)

            blocks.append(
                Stripped(
                    f"""\
test({title}, () => {{
{I}expect(() => AasCommon.parseSafeInt({text_literal})).toThrow();
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
