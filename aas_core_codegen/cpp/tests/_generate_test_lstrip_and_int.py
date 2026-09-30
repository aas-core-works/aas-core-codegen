"""Generate the unit tests for ``str.lstrip`` and ``int`` on strings."""

from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped
from aas_core_codegen.cpp import common as cpp_common
from aas_core_codegen.cpp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
)
from aas_core_codegen.intermediate import uses as intermediate_uses


# fmt: off
@require(
    lambda symbol_table:
    intermediate_uses.lstrip_call(symbol_table) or intermediate_uses.int_call(symbol_table)
)
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate_implementation(
    symbol_table: intermediate.SymbolTable, library_namespace: Stripped
) -> str:
    """
    Generate the unit tests for ``str.lstrip`` and ``int`` on strings.

    All the SDKs test against the very same cases, see
    :py:mod:`aas_core_codegen.tests_common`.
    """
    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            """\
/**
 * Test `str.lstrip` and `int` on strings as used in the transpiled code.
 *
 * The transpiled `str.lstrip` follows the Python implementation, since Python is
 * the language of the meta-model specifications. Hence, it strips
 * the characters (code points).
 *
 * The built-in `int` is transpiled to <code>common::ParseSafeInt</code>,
 * which is stricter than the Python `int`. It accepts only an optional sign
 * followed by the ASCII digits, and only the safe integers, <em>i.e.</em>,
 * the integers within <code>-(2^53 - 1)</code> and <code>2^53 - 1</code>.
 * Otherwise, it throws.
 *
 * All the SDKs test against the very same cases.
 */"""
        ),
        Stripped(
            f"""\
#include "{include_prefix_path}/common.hpp"

#pragma warning(push, 0)
#include <cstdint>
#include <stdexcept>
#pragma warning(pop)

#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>

namespace our = {library_namespace};"""
        ),
    ]  # type: List[Stripped]

    if intermediate_uses.lstrip_call(symbol_table):
        for i, (text, chars, expected) in enumerate(tests_common.LSTRIP_CASES):
            name = cpp_common.string_literal(
                f"Test LStrip {i}: {text!r}.lstrip({chars!r}) gives {expected!r}"
            )

            blocks.append(
                Stripped(
                    f"""\
TEST_CASE({name}) {{
{I}REQUIRE(
{II}our::common::LStrip(
{III}{cpp_common.wstring_literal(text)},
{III}{cpp_common.wstring_literal(chars)}
{II})
{II}== {cpp_common.wstring_literal(expected)}
{I});
}}"""
                )
            )

    if intermediate_uses.int_call(symbol_table):
        for i, (text, expected_int) in enumerate(tests_common.PARSE_INT_CASES):
            name = cpp_common.string_literal(
                f"Test ParseSafeInt {i}: {text!r} gives {expected_int}"
            )

            blocks.append(
                Stripped(
                    f"""\
TEST_CASE({name}) {{
{I}REQUIRE(
{II}our::common::ParseSafeInt({cpp_common.wstring_literal(text)})
{II}== INT64_C({expected_int})
{I});
}}"""
                )
            )

        for i, text in enumerate(tests_common.PARSE_INT_INVALID_CASES):
            name = cpp_common.string_literal(
                f"Test ParseSafeInt on invalid {i}: {text!r}"
            )

            blocks.append(
                Stripped(
                    f"""\
TEST_CASE({name}) {{
{I}REQUIRE_THROWS_AS(
{II}our::common::ParseSafeInt({cpp_common.wstring_literal(text)}),
{II}std::invalid_argument
{I});
}}"""
                )
            )

    blocks.append(cpp_common.WARNING)

    return "\n\n".join(blocks) + "\n"
