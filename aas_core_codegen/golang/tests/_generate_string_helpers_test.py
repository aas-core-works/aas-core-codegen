"""Generate the unit tests for the helpers of ``len``, slicing, ``find`` and comparing."""

import io
import re
from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, string_helper_cases
from aas_core_codegen.common import Stripped
from aas_core_codegen.intermediate import (
    type_inference as intermediate_type_inference,
    uses as intermediate_uses,
)
from aas_core_codegen.golang import common as golang_common
from aas_core_codegen.golang.common import INDENT as I, INDENT2 as II


def _function_name(prefix: str, description: str) -> str:
    """Derive the name of a test function from the ``description`` of a case."""
    words = re.split(r"[^a-zA-Z0-9]+", description)
    return f"Test{prefix}" + "".join(word.capitalize() for word in words if word)


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
    repo_url: Stripped,
    symbol_table: intermediate.SymbolTable,
    type_inference: intermediate_type_inference.TypeInference,
) -> str:
    """Generate the unit tests for the helpers of ``len``, slicing, ``find`` and comparing."""
    uses_len_slicing_or_find = intermediate_uses.len_slicing_or_find(symbol_table)
    uses_comparisons = intermediate_uses.string_ordering(type_inference)

    imports = []  # type: List[str]
    if uses_comparisons:
        imports.append('"strings"')

    imports.append('"testing"')

    if uses_len_slicing_or_find:
        imports.append(f'ourcommon "{repo_url}/common"')

    imports_joined = "\n".join(f"{I}{an_import}" for an_import in imports)

    blocks = [
        Stripped(
            """\
// Test the operations on strings.
//
// The operations follow the Python implementation, since Python is
// the language of the meta-model specifications. Hence, they work on
// the characters (code points) of the strings. The expected values have been
// computed with Python, and all the SDKs test against the very same cases.
package common_string_helpers_test"""
        ),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{imports_joined}
)"""
        ),
    ]  # type: List[Stripped]

    if uses_len_slicing_or_find:
        for len_case in string_helper_cases.LEN_CASES:
            explanation = golang_common.string_literal(
                f"Expected {len_case.python_expression()} to give "
                f"{len_case.expected} ({len_case.description}), but got %d"
            )

            # NOTE (mristin):
            # We call the helper just as the transpiled code does.
            blocks.append(
                Stripped(
                    f"""\
func {_function_name("Len", len_case.description)}(t *testing.T) {{
{I}got := ourcommon.LenStr({golang_common.string_literal(len_case.text)})
{I}if got != {len_case.expected} {{
{II}t.Errorf({explanation}, got)
{I}}}
}}"""
                )
            )

        for slice_case in string_helper_cases.SLICE_CASES:
            text = golang_common.string_literal(slice_case.text)
            start = "0" if slice_case.start is None else str(slice_case.start)

            # NOTE (mristin):
            # We call the helper just as the transpiled code does.
            call = (
                f"ourcommon.SliceStrFrom({text}, {start})"
                if slice_case.end is None
                else f"ourcommon.SliceStr({text}, {start}, {slice_case.end})"
            )

            explanation = golang_common.string_literal(
                f"Expected {slice_case.python_expression()} to give "
                f"{slice_case.expected!r} ({slice_case.description}), but got %q"
            )

            blocks.append(
                Stripped(
                    f"""\
func {_function_name("Slice", slice_case.description)}(t *testing.T) {{
{I}got := {call}
{I}if got != {golang_common.string_literal(slice_case.expected)} {{
{II}t.Errorf({explanation}, got)
{I}}}
}}"""
                )
            )

        for find_case in string_helper_cases.FIND_CASES:
            text = golang_common.string_literal(find_case.text)
            sub = golang_common.string_literal(find_case.sub)

            # NOTE (mristin):
            # We call the helper just as the transpiled code does.
            start = "0" if find_case.start is None else str(find_case.start)
            call = f"ourcommon.FindStr({text}, {sub}, {start})"

            explanation = golang_common.string_literal(
                f"Expected {find_case.python_expression()} to give "
                f"{find_case.expected} ({find_case.description}), but got %d"
            )

            blocks.append(
                Stripped(
                    f"""\
func {_function_name("Find", find_case.description)}(t *testing.T) {{
{I}got := {call}
{I}if got != {find_case.expected} {{
{II}t.Errorf({explanation}, got)
{I}}}
}}"""
                )
            )

    if uses_comparisons:
        for compare_case in string_helper_cases.COMPARE_CASES:
            left = golang_common.string_literal(compare_case.left)
            right = golang_common.string_literal(compare_case.right)

            explanation = golang_common.string_literal(
                f"Expected {compare_case.python_expression()} to give "
                f"{compare_case.expected} ({compare_case.description}), but got %d"
            )

            blocks.append(
                Stripped(
                    f"""\
func {_function_name("Compare", compare_case.description)}(t *testing.T) {{
{I}got := strings.Compare({left}, {right})
{I}if got != {compare_case.expected} {{
{II}t.Errorf({explanation}, got)
{I}}}
}}"""
                )
            )

    blocks.append(golang_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
