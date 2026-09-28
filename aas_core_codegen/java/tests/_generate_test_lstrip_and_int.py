"""Generate code to test ``str.lstrip`` and ``int`` as used in the verification."""

from typing import List

from icontract import require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped, indent_but_first_line
from aas_core_codegen.java import common as java_common
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
)


# fmt: off
@require(
    lambda symbol_table:
    intermediate.uses_lstrip(symbol_table) or intermediate.uses_int(symbol_table)
)
# fmt: on
def generate(
    package: java_common.PackageIdentifier,
    symbol_table: intermediate.SymbolTable,
) -> List[java_common.JavaFile]:
    """
    Generate code to test ``str.lstrip`` and ``int`` as used in the verification.

    The transpiled ``lstrip`` follows the Python semantics, while the transpiled
    ``int`` is stricter than the Python ``int`` so that all the SDKs behave the same.
    The tests are generated from the same cases for all the SDKs, see
    :py:mod:`aas_core_codegen.tests_common`.
    """
    blocks = []  # type: List[Stripped]

    if intermediate.uses_lstrip(symbol_table):
        for i, (text, chars, expected) in enumerate(tests_common.LSTRIP_CASES):
            blocks.append(
                Stripped(
                    f"""\
@Test
public void testLstrip{i}() {{
{I}assertEquals(
{II}{java_common.string_literal(expected)},
{II}StringHelpers.lstrip(
{III}{java_common.string_literal(text)},
{III}{java_common.string_literal(chars)}));
}} // public void testLstrip{i}"""
                )
            )

    if intermediate.uses_int(symbol_table):
        for i, (text, expected_int) in enumerate(tests_common.PARSE_INT_CASES):
            blocks.append(
                Stripped(
                    f"""\
@Test
public void testInt{i}() {{
{I}assertEquals(
{II}{expected_int}L,
{II}StringHelpers.parseSafeInt({java_common.string_literal(text)}));
}} // public void testInt{i}"""
                )
            )

        for i, text in enumerate(tests_common.PARSE_INT_INVALID_CASES):
            blocks.append(
                Stripped(
                    f"""\
@Test
public void testIntInvalid{i}() {{
{I}assertThrows(
{II}IllegalArgumentException.class,
{II}() -> StringHelpers.parseSafeInt({java_common.string_literal(text)}));
}} // public void testIntInvalid{i}"""
                )
            )

    blocks_joined = "\n\n".join(blocks)

    return [
        java_common.JavaFile(
            "TestLstripAndInt.java",
            f"""\
{java_common.WARNING}

package {package}.tests;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import {package}.common.StringHelpers;
import org.junit.jupiter.api.Test;

/**
 * Test {{@code str.lstrip}} and {{@code int}} as used in the verification.
 *
 * <p>The transpiled {{@code lstrip}} follows the Python implementation, since
 * Python is the language of the meta-model specifications. Hence, it strips
 * the characters (code points), and not the UTF-16 code units.
 *
 * <p>The transpiled {{@code int}} is stricter than the Python {{@code int}}. It
 * accepts only an optional sign followed by the ASCII digits, and only the safe
 * integers, <i>i.e.</i>, the integers within {{@code -(2^53 - 1)}} and
 * {{@code 2^53 - 1}}. Otherwise, it throws.
 *
 * <p>The other SDKs test against the very same cases.
 */
public class TestLstripAndInt {{
{I}{indent_but_first_line(blocks_joined, I)}
}} // class TestLstripAndInt

// package {package}.tests

{java_common.WARNING}
""",
        )
    ]


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
