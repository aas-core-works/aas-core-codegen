"""Generate code to test the assignments to the properties and the list items."""

import io
from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped
from aas_core_codegen.typescript import common as typescript_common
from aas_core_codegen.typescript.common import (
    INDENT as I,
    INDENT2 as II,
)


# fmt: off
@require(
    lambda symbol_table:
    tests_common.defines_assignment_target_verifications(symbol_table)
)
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable) -> str:
    """
    Generate code to test the assignments to the properties and the list items.

    The tests call the verification functions of the meta-model
    ``dev/test_data/common_meta_models/assignment_targets.py``, see
    :py:mod:`aas_core_codegen.tests_common`.
    """
    blocks = [
        Stripped(
            """\
/**
 * Test the assignments to the properties and to the items of the lists
 * in the verification functions.
 *
 * @remarks
 *
 * The meta-model is written in Python, so the assignments follow the Python
 * semantics: the objects and the lists are shared by reference, a negative
 * index counts from the end of the list, and an index out of range throws
 * instead of growing the array.
 */"""
        ),
        typescript_common.WARNING,
        Stripped(
            """\
import * as AasTypes from "../src/types";
import * as AasVerification from "../src/verification";"""
        ),
        Stripped(
            f"""\
test("setText", () => {{
{I}const item = new AasTypes.Item("a", ["b"]);
{I}AasVerification.setText(item, "x");
{I}expect(item.text).toBe("x");
}});"""
        ),
        Stripped(
            f"""\
test("setMaybeText", () => {{
{I}const item = new AasTypes.Item("a", []);
{I}AasVerification.setMaybeText(item, "x");
{I}expect(item.maybeText).toBe("x");
}});"""
        ),
        Stripped(
            f"""\
test("copyMaybeTextAndSetMaybeKind", () => {{
{I}const item = new AasTypes.Item("a", [], "old");
{I}const other = new AasTypes.Item("b", []);
{I}AasVerification.copyMaybeTextAndSetMaybeKind(item, other);
{I}expect(item.maybeText).toBeNull();
{I}expect(item.maybeKind).toBe(AasTypes.Kind.Alpha);
}});"""
        ),
        Stripped(
            f"""\
test("setTextThroughAlias", () => {{
{I}const item = new AasTypes.Item("a", []);
{I}AasVerification.setTextThroughAlias(item, "x");
{I}expect(item.text).toBe("x");
}});"""
        ),
        Stripped(
            f"""\
test("setTexts", () => {{
{I}const item = new AasTypes.Item("a", ["b"]);
{I}const texts = ["x", "y"];
{I}AasVerification.setTexts(item, texts);
{I}expect(item.texts).toBe(texts);
}});"""
        ),
        Stripped(
            f"""\
test("setFirstAndLastText", () => {{
{I}const item = new AasTypes.Item("a", ["a", "b", "c"]);
{I}AasVerification.setFirstAndLastText(item, "x");
{I}expect(item.texts).toStrictEqual(["x", "b", "x"]);
}});"""
        ),
        Stripped(
            f"""\
test("setTextThroughListAlias", () => {{
{I}const item = new AasTypes.Item("a", ["a", "b", "c"]);
{I}AasVerification.setTextThroughListAlias(item, "x");
{I}expect(item.texts).toStrictEqual(["a", "x", "c"]);
}});"""
        ),
        Stripped(
            f"""\
test("setNumbers", () => {{
{I}const numbers = [1, 2, 3, 4];
{I}AasVerification.setNumbers(numbers, 10);
{I}expect(numbers).toStrictEqual([10, 2, 5, 4]);
}});"""
        ),
        Stripped(
            f"""\
test("setNumbers with an index out of range", () => {{
{I}const numbers = [1];
{I}expect(() => AasVerification.setNumbers(numbers, 10)).toThrow(RangeError);
{I}expect(numbers.length).toBe(1);
}});"""
        ),
        Stripped(
            f"""\
test("setNestedText", () => {{
{I}const items = [
{II}new AasTypes.Item("a", ["a", "b"]),
{II}new AasTypes.Item("b", ["c"])
{I}];
{I}AasVerification.setNestedText(items, "x");
{I}expect(items[0].texts).toStrictEqual(["a", "x"]);
{I}expect(items[1].text).toBe("x");
}});"""
        ),
        Stripped(
            f"""\
test("replaceFirstItem", () => {{
{I}const items = [
{II}new AasTypes.Item("a", []),
{II}new AasTypes.Item("b", [])
{I}];
{I}const item = new AasTypes.Item("c", []);
{I}AasVerification.replaceFirstItem(items, item);
{I}expect(items[0]).toBe(item);
{I}expect(items.length).toBe(2);
}});"""
        ),
        Stripped(
            f"""\
test("setTextsInLoops", () => {{
{I}const items = [
{II}new AasTypes.Item("a", ["a"]),
{II}new AasTypes.Item("b", ["b", "c"])
{I}];
{I}AasVerification.setTextsInLoops(items, "x");
{I}for (const item of items) {{
{II}expect(item.text).toBe("x");
{II}expect(item.texts[0]).toBe("x");
{I}}}
}});"""
        ),
        typescript_common.WARNING,
    ]  # type: List[Stripped]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
