"""Generate code to test the assignments to the properties and the list items."""

from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped, indent_but_first_line
from aas_core_codegen.python import common as python_common
from aas_core_codegen.python.common import (
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
    symbol_table: intermediate.SymbolTable,
    qualified_module_name: python_common.QualifiedModuleName,
) -> str:
    """
    Generate code to test the assignments to the properties and the list items.

    The tests call the verification functions of the meta-model
    ``dev/test_data/common_meta_models/assignment_targets.py``, see
    :py:mod:`aas_core_codegen.tests_common`.

    The ``qualified_module_name`` indicates the fully-qualified name of the base module.
    """
    methods = [
        Stripped(
            f"""\
def test_set_text(self) -> None:
{I}item = aas_types.Item("a", ["b"])
{I}aas_verification.set_text(item, "x")
{I}self.assertEqual("x", item.text)"""
        ),
        Stripped(
            f"""\
def test_set_maybe_text(self) -> None:
{I}item = aas_types.Item("a", [])
{I}aas_verification.set_maybe_text(item, "x")
{I}self.assertEqual("x", item.maybe_text)"""
        ),
        Stripped(
            f"""\
def test_copy_maybe_text_and_set_maybe_kind(self) -> None:
{I}item = aas_types.Item("a", [], maybe_text="old")
{I}other = aas_types.Item("b", [])
{I}aas_verification.copy_maybe_text_and_set_maybe_kind(item, other)
{I}self.assertIsNone(item.maybe_text)
{I}self.assertEqual(aas_types.Kind.ALPHA, item.maybe_kind)"""
        ),
        Stripped(
            f"""\
def test_set_text_through_alias(self) -> None:
{I}item = aas_types.Item("a", [])
{I}aas_verification.set_text_through_alias(item, "x")
{I}self.assertEqual("x", item.text)"""
        ),
        Stripped(
            f"""\
def test_set_texts(self) -> None:
{I}item = aas_types.Item("a", ["b"])
{I}texts = ["x", "y"]
{I}aas_verification.set_texts(item, texts)
{I}self.assertIs(texts, item.texts)"""
        ),
        Stripped(
            f"""\
def test_set_first_and_last_text(self) -> None:
{I}item = aas_types.Item("a", ["a", "b", "c"])
{I}aas_verification.set_first_and_last_text(item, "x")
{I}self.assertEqual(["x", "b", "x"], item.texts)"""
        ),
        Stripped(
            f"""\
def test_set_text_through_list_alias(self) -> None:
{I}item = aas_types.Item("a", ["a", "b", "c"])
{I}aas_verification.set_text_through_list_alias(item, "x")
{I}self.assertEqual(["a", "x", "c"], item.texts)"""
        ),
        Stripped(
            f"""\
def test_set_numbers(self) -> None:
{I}numbers = [1, 2, 3, 4]
{I}aas_verification.set_numbers(numbers, 10)
{I}self.assertEqual([10, 2, 5, 4], numbers)"""
        ),
        Stripped(
            f"""\
def test_set_numbers_out_of_range(self) -> None:
{I}with self.assertRaises(IndexError):
{II}aas_verification.set_numbers([1], 10)"""
        ),
        Stripped(
            f"""\
def test_set_nested_text(self) -> None:
{I}items = [aas_types.Item("a", ["a", "b"]), aas_types.Item("b", ["c"])]
{I}aas_verification.set_nested_text(items, "x")
{I}self.assertEqual(["a", "x"], items[0].texts)
{I}self.assertEqual("x", items[1].text)"""
        ),
        Stripped(
            f"""\
def test_replace_first_item(self) -> None:
{I}items = [aas_types.Item("a", []), aas_types.Item("b", [])]
{I}item = aas_types.Item("c", [])
{I}aas_verification.replace_first_item(items, item)
{I}self.assertIs(item, items[0])
{I}self.assertEqual(2, len(items))"""
        ),
        Stripped(
            f"""\
def test_set_texts_in_loops(self) -> None:
{I}items = [aas_types.Item("a", ["a"]), aas_types.Item("b", ["b", "c"])]
{I}aas_verification.set_texts_in_loops(items, "x")
{I}for item in items:
{II}self.assertEqual("x", item.text)
{II}self.assertEqual("x", item.texts[0])"""
        ),
    ]  # type: List[Stripped]

    methods_joined = "\n\n".join(methods)

    blocks = [
        Stripped(
            '''\
"""
Test the assignments to the properties and to the items of the lists
in the verification functions.

The Python SDK uses the native assignments. We still generate the tests so that
the clients can compare the behavior against the other SDKs.
"""'''
        ),
        python_common.WARNING,
        Stripped(
            """\
# pylint: disable=missing-docstring"""
        ),
        Stripped(
            f"""\
import unittest

import {qualified_module_name}.types as aas_types
import {qualified_module_name}.verification as aas_verification"""
        ),
        Stripped(
            f"""\
class TestAssignmentTargets(unittest.TestCase):
{I}{indent_but_first_line(methods_joined, I)}"""
        ),
        Stripped(
            f"""\
if __name__ == "__main__":
{I}unittest.main()"""
        ),
        python_common.WARNING,
    ]

    return "\n\n\n".join(blocks) + "\n"


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
