"""Generate the unit tests for the helpers of ``len``, slicing, ``find`` and comparing."""

import io
from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, string_helper_cases
from aas_core_codegen.common import Stripped
from aas_core_codegen.intermediate import (
    type_inference as intermediate_type_inference,
    uses as intermediate_uses,
)
from aas_core_codegen.typescript import common as typescript_common
from aas_core_codegen.typescript.common import INDENT as I, INDENT2 as II


def _generate_len_test(case: string_helper_cases.LenCase) -> Stripped:
    """Generate the test of a single ``len`` ``case``."""
    name = typescript_common.string_literal(
        f"{case.python_expression()} gives {case.expected}: {case.description}"
    )

    text = typescript_common.string_literal(case.text)

    return Stripped(
        f"""\
test({name}, () => {{
{I}expect(OurCommon.lenStr({text})).toStrictEqual({case.expected});
}});"""
    )


def _generate_slice_test(case: string_helper_cases.SliceCase) -> Stripped:
    """Generate the test of a single slicing ``case``."""
    name = typescript_common.string_literal(
        f"{case.python_expression()} gives {case.expected!r}: {case.description}"
    )

    # NOTE (mristin):
    # We call the helper just as the transpiled code does.
    args = [
        typescript_common.string_literal(case.text),
        "0" if case.start is None else str(case.start),
    ]
    if case.end is not None:
        args.append(str(case.end))

    expected = typescript_common.string_literal(case.expected)

    return Stripped(
        f"""\
test({name}, () => {{
{I}expect(OurCommon.sliceStr({", ".join(args)})).toStrictEqual({expected});
}});"""
    )


def _generate_find_test(case: string_helper_cases.FindCase) -> Stripped:
    """Generate the test of a single ``find`` ``case``."""
    name = typescript_common.string_literal(
        f"{case.python_expression()} gives {case.expected}: {case.description}"
    )

    text = typescript_common.string_literal(case.text)
    sub = typescript_common.string_literal(case.sub)

    # NOTE (mristin):
    # We call the helper just as the transpiled code does.
    args = [text, sub]  # type: List[str]
    if case.start is not None:
        args.append(str(case.start))

    call = f"OurCommon.findStr({', '.join(args)})"

    return Stripped(
        f"""\
test({name}, () => {{
{I}expect({call}).toStrictEqual({case.expected});
}});"""
    )


def _generate_compare_test(case: string_helper_cases.CompareCase) -> Stripped:
    """Generate the test of a single comparison ``case``."""
    name = typescript_common.string_literal(
        f"{case.python_expression()} gives {case.expected}: {case.description}"
    )

    left = typescript_common.string_literal(case.left)
    right = typescript_common.string_literal(case.right)

    return Stripped(
        f"""\
test({name}, () => {{
{I}expect(
{II}Math.sign(OurCommon.compareByCodePoints({left}, {right}))
{I}).toStrictEqual({case.expected});
}});"""
    )


# fmt: off
@require(
    lambda symbol_table, type_inference:
    intermediate_uses.len_slicing_or_find(symbol_table)
    or intermediate_uses.string_ordering(type_inference)
)
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable,
    type_inference: intermediate_type_inference.TypeInference,
) -> str:
    """Generate the unit tests for the helpers of ``len``, slicing, ``find`` and comparing."""
    blocks = [
        Stripped(
            """\
/**
 * Test the operations on strings.
 *
 * @remarks
 * The operations follow the Python implementation, since Python is
 * the language of the meta-model specifications. Hence, they work on
 * the characters (code points) of the strings. The expected values have been
 * computed with Python, and all the SDKs test against the very same cases.
 */"""
        ),
        typescript_common.WARNING,
        Stripped('import * as OurCommon from "../src/common";'),
    ]  # type: List[Stripped]

    if intermediate_uses.len_slicing_or_find(symbol_table):
        for len_case in string_helper_cases.LEN_CASES:
            blocks.append(_generate_len_test(len_case))

        for slice_case in string_helper_cases.SLICE_CASES:
            blocks.append(_generate_slice_test(slice_case))

        for find_case in string_helper_cases.FIND_CASES:
            blocks.append(_generate_find_test(find_case))

    if intermediate_uses.string_ordering(type_inference):
        for compare_case in string_helper_cases.COMPARE_CASES:
            blocks.append(_generate_compare_test(compare_case))

    blocks.append(typescript_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()
