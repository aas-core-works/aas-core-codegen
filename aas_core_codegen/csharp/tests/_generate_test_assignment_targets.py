"""Generate code to test the assignments to the properties and the list items."""

from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped, indent_but_first_line
from aas_core_codegen.csharp import common as csharp_common
from aas_core_codegen.csharp.common import (
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
def generate(
    namespace: csharp_common.NamespaceIdentifier,
    symbol_table: intermediate.SymbolTable,
) -> str:
    """
    Generate code to test the assignments to the properties and the list items.

    The tests call the verification functions of the meta-model
    ``dev/test_data/common_meta_models/assignment_targets.py``, see
    :py:mod:`aas_core_codegen.tests_common`.

    The ``namespace`` indicates the fully-qualified name of the base project.
    """
    blocks = [
        Stripped(
            f"""\
[Test]
public void Test_set_text()
{{
{I}var item = new Aas.Item("a", new List<string> {{ "b" }});
{I}Aas.Verification.SetText(item, "x");
{I}Assert.AreEqual("x", item.Text);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_maybe_text()
{{
{I}var item = new Aas.Item("a", new List<string>());
{I}Aas.Verification.SetMaybeText(item, "x");
{I}Assert.AreEqual("x", item.MaybeText);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_copy_maybe_text_and_set_maybe_kind()
{{
{I}var item = new Aas.Item("a", new List<string>(), "old");
{I}var other = new Aas.Item("b", new List<string>());
{I}Aas.Verification.CopyMaybeTextAndSetMaybeKind(item, other);
{I}Assert.IsNull(item.MaybeText);
{I}Assert.AreEqual(Aas.Kind.Alpha, item.MaybeKind);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_text_through_alias()
{{
{I}var item = new Aas.Item("a", new List<string>());
{I}Aas.Verification.SetTextThroughAlias(item, "x");
{I}Assert.AreEqual("x", item.Text);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_texts()
{{
{I}var item = new Aas.Item("a", new List<string> {{ "b" }});
{I}var texts = new List<string> {{ "x", "y" }};
{I}Aas.Verification.SetTexts(item, texts);
{I}Assert.AreSame(texts, item.Texts);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_first_and_last_text()
{{
{I}var item = new Aas.Item("a", new List<string> {{ "a", "b", "c" }});
{I}Aas.Verification.SetFirstAndLastText(item, "x");
{I}CollectionAssert.AreEqual(
{II}new List<string> {{ "x", "b", "x" }},
{II}item.Texts);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_text_through_list_alias()
{{
{I}var item = new Aas.Item("a", new List<string> {{ "a", "b", "c" }});
{I}Aas.Verification.SetTextThroughListAlias(item, "x");
{I}CollectionAssert.AreEqual(
{II}new List<string> {{ "a", "x", "c" }},
{II}item.Texts);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_numbers()
{{
{I}var numbers = new List<long> {{ 1, 2, 3, 4 }};
{I}Aas.Verification.SetNumbers(numbers, 10);
{I}CollectionAssert.AreEqual(new List<long> {{ 10, 2, 5, 4 }}, numbers);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_numbers_out_of_range()
{{
{I}var numbers = new List<long> {{ 1 }};
{I}Assert.Throws<System.ArgumentOutOfRangeException>(
{II}() => Aas.Verification.SetNumbers(numbers, 10));
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_nested_text()
{{
{I}var items = new List<Aas.IItem>
{I}{{
{II}new Aas.Item("a", new List<string> {{ "a", "b" }}),
{II}new Aas.Item("b", new List<string> {{ "c" }})
{I}}};
{I}Aas.Verification.SetNestedText(items, "x");
{I}CollectionAssert.AreEqual(new List<string> {{ "a", "x" }}, items[0].Texts);
{I}Assert.AreEqual("x", items[1].Text);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_replace_first_item()
{{
{I}var items = new List<Aas.IItem>
{I}{{
{II}new Aas.Item("a", new List<string>()),
{II}new Aas.Item("b", new List<string>())
{I}}};
{I}var item = new Aas.Item("c", new List<string>());
{I}Aas.Verification.ReplaceFirstItem(items, item);
{I}Assert.AreSame(item, items[0]);
{I}Assert.AreEqual(2, items.Count);
}}"""
        ),
        Stripped(
            f"""\
[Test]
public void Test_set_texts_in_loops()
{{
{I}var items = new List<Aas.IItem>
{I}{{
{II}new Aas.Item("a", new List<string> {{ "a" }}),
{II}new Aas.Item("b", new List<string> {{ "b", "c" }})
{I}}};
{I}Aas.Verification.SetTextsInLoops(items, "x");
{I}foreach (var item in items)
{I}{{
{II}Assert.AreEqual("x", item.Text);
{II}Assert.AreEqual("x", item.Texts[0]);
{I}}}
}}"""
        ),
    ]  # type: List[Stripped]

    blocks_joined = "\n\n".join(blocks)

    return f"""\
{csharp_common.WARNING}

using Aas = {namespace};  // renamed

using NUnit.Framework;  // can't alias
using System.Collections.Generic;  // can't alias

namespace {namespace}.Tests
{{
{I}/// <summary>
{I}/// Test the assignments to the properties and to the items of the lists
{I}/// in the verification functions.
{I}/// </summary>
{I}/// <remarks>
{I}/// The meta-model is written in Python, so the assignments follow the Python
{I}/// semantics: the objects and the lists are shared by reference, and
{I}/// a negative index counts from the end of the list.
{I}/// </remarks>
{I}public class TestAssignmentTargets
{I}{{
{II}{indent_but_first_line(blocks_joined, II)}
{I}}}  // class TestAssignmentTargets
}}  // namespace {namespace}.Tests

{csharp_common.WARNING}
"""


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
