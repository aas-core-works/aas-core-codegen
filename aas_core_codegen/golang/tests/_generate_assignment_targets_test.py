"""Generate code to test the assignments to the properties and the list items."""

import io
from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped
from aas_core_codegen.golang import common as golang_common
from aas_core_codegen.golang.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
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
def generate(symbol_table: intermediate.SymbolTable, repo_url: Stripped) -> str:
    """
    Generate code to test the assignments to the properties and the list items.

    The tests call the verification functions of the meta-model
    ``dev/test_data/common_meta_models/assignment_targets.py``, see
    :py:mod:`aas_core_codegen.tests_common`.
    """
    blocks = [
        Stripped("package verification_test"),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{I}"reflect"
{I}"testing"
{I}aascommon "{repo_url}/common"
{I}aastypes "{repo_url}/types"
{I}aasverification "{repo_url}/verification"
)"""
        ),
        Stripped(
            """\
// The meta-model is written in Python, so the assignments follow the Python
// semantics: the objects and the lists are shared by reference, and a negative
// index counts from the end of the list."""
        ),
        Stripped(
            f"""\
func TestSetText(t *testing.T) {{
{I}item := aastypes.NewItem("a", []string{{"b"}})
{I}aasverification.SetText(item, "x")
{I}if item.Text() != "x" {{
{II}t.Fatalf("Expected the text \\"x\\", but got: %v", item.Text())
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestSetMaybeText(t *testing.T) {{
{I}item := aastypes.NewItem("a", []string{{}})
{I}aasverification.SetMaybeText(item, "x")
{I}if item.MaybeText() == nil || *item.MaybeText() != "x" {{
{II}t.Fatalf("Expected the maybe-text \\"x\\", but got: %v", item.MaybeText())
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestCopyMaybeTextAndSetMaybeKind(t *testing.T) {{
{I}item := aastypes.NewItem("a", []string{{}})
{I}item.SetMaybeText(aascommon.NewAndPointTo("old"))
{I}other := aastypes.NewItem("b", []string{{}})
{I}aasverification.CopyMaybeTextAndSetMaybeKind(item, other)
{I}if item.MaybeText() != nil {{
{II}t.Fatalf("Expected no maybe-text, but got: %v", *item.MaybeText())
{I}}}
{I}if item.MaybeKind() == nil || *item.MaybeKind() != aastypes.KindAlpha {{
{II}t.Fatalf("Expected the maybe-kind Alpha, but got: %v", item.MaybeKind())
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestSetTextThroughAlias(t *testing.T) {{
{I}item := aastypes.NewItem("a", []string{{}})
{I}aasverification.SetTextThroughAlias(item, "x")
{I}if item.Text() != "x" {{
{II}t.Fatalf("Expected the text \\"x\\", but got: %v", item.Text())
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestSetTexts(t *testing.T) {{
{I}item := aastypes.NewItem("a", []string{{"b"}})
{I}texts := []string{{"x", "y"}}
{I}aasverification.SetTexts(item, texts)
{I}if &item.Texts()[0] != &texts[0] {{
{II}t.Fatalf("Expected the texts to share the array, but got: %v", item.Texts())
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestSetFirstAndLastText(t *testing.T) {{
{I}item := aastypes.NewItem("a", []string{{"a", "b", "c"}})
{I}aasverification.SetFirstAndLastText(item, "x")
{I}expected := []string{{"x", "b", "x"}}
{I}if !reflect.DeepEqual(expected, item.Texts()) {{
{II}t.Fatalf("Expected the texts %v, but got: %v", expected, item.Texts())
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestSetTextThroughListAlias(t *testing.T) {{
{I}item := aastypes.NewItem("a", []string{{"a", "b", "c"}})
{I}aasverification.SetTextThroughListAlias(item, "x")
{I}expected := []string{{"a", "x", "c"}}
{I}if !reflect.DeepEqual(expected, item.Texts()) {{
{II}t.Fatalf("Expected the texts %v, but got: %v", expected, item.Texts())
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestSetNumbers(t *testing.T) {{
{I}numbers := []int64{{1, 2, 3, 4}}
{I}aasverification.SetNumbers(numbers, 10)
{I}expected := []int64{{10, 2, 5, 4}}
{I}if !reflect.DeepEqual(expected, numbers) {{
{II}t.Fatalf("Expected the numbers %v, but got: %v", expected, numbers)
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestSetNumbersOutOfRange(t *testing.T) {{
{I}defer func() {{
{II}if recover() == nil {{
{III}t.Fatal("Expected a panic on the index out of range, but got none")
{II}}}
{I}}}()

{I}aasverification.SetNumbers([]int64{{1}}, 10)
}}"""
        ),
        Stripped(
            f"""\
func TestSetNestedText(t *testing.T) {{
{I}items := []aastypes.IItem{{
{II}aastypes.NewItem("a", []string{{"a", "b"}}),
{II}aastypes.NewItem("b", []string{{"c"}}),
{I}}}
{I}aasverification.SetNestedText(items, "x")
{I}expected := []string{{"a", "x"}}
{I}if !reflect.DeepEqual(expected, items[0].Texts()) {{
{II}t.Fatalf("Expected the texts %v, but got: %v", expected, items[0].Texts())
{I}}}
{I}if items[1].Text() != "x" {{
{II}t.Fatalf("Expected the text \\"x\\", but got: %v", items[1].Text())
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestReplaceFirstItem(t *testing.T) {{
{I}items := []aastypes.IItem{{
{II}aastypes.NewItem("a", []string{{}}),
{II}aastypes.NewItem("b", []string{{}}),
{I}}}
{I}item := aastypes.NewItem("c", []string{{}})
{I}aasverification.ReplaceFirstItem(items, item)
{I}if items[0] != item || len(items) != 2 {{
{II}t.Fatalf("Expected the first item to be replaced, but got: %v", items)
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestSetTextsInLoops(t *testing.T) {{
{I}items := []aastypes.IItem{{
{II}aastypes.NewItem("a", []string{{"a"}}),
{II}aastypes.NewItem("b", []string{{"b", "c"}}),
{I}}}
{I}aasverification.SetTextsInLoops(items, "x")
{I}for _, item := range items {{
{II}if item.Text() != "x" || item.Texts()[0] != "x" {{
{III}t.Fatalf(
{IIII}"Expected the text and the first of the texts to be \\"x\\", " +
{IIIII}"but got: %v and %v",
{IIII}item.Text(),
{IIII}item.Texts(),
{III})
{II}}}
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func TestNewAndPointToCopies(t *testing.T) {{
{I}text := "a"
{I}pointer := aascommon.NewAndPointTo(text)
{I}text = "b"
{I}if *pointer != "a" || text != "b" {{
{II}t.Fatalf("Expected the pointed value \\"a\\", but got: %v", *pointer)
{I}}}
}}"""
        ),
        golang_common.WARNING,
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
