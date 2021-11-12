import unittest
from typing import Sequence, List

from aas_core_csharp_codegen.rdf_shacl import (
    _description as rdf_shacl_description
)


def tokens_are_equal(
        that: Sequence[rdf_shacl_description.Token],
        other: Sequence[rdf_shacl_description.Token]
) -> bool:
    if len(that) != len(other):
        return False

    for me, you in zip(that, other):
        if type(me) != type(you):
            return False

        if (
                isinstance(me, rdf_shacl_description.TokenText)
        ):
            assert isinstance(you, rdf_shacl_description.TokenText)
            if me.content != you.content:
                return False

    return True


class Test_without_redundant_breaks(unittest.TestCase):
    def test_empty(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks([])
        expected = []  # type: List[rdf_shacl_description.Token]
        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}")

    def test_text(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [rdf_shacl_description.TokenText("something")])

        expected = [rdf_shacl_description.TokenText("something")]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}")

    def test_consecutive_line_breaks(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [
                rdf_shacl_description.TokenText("something"),
                rdf_shacl_description.TokenLineBreak(),
                rdf_shacl_description.TokenLineBreak(),
                rdf_shacl_description.TokenText("else")
            ])

        expected = [
            rdf_shacl_description.TokenText("something"),
            rdf_shacl_description.TokenLineBreak(),
            rdf_shacl_description.TokenText("else")
        ]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}")

    def test_consecutive_paragraph_breaks(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [
                rdf_shacl_description.TokenText("something"),
                rdf_shacl_description.TokenParagraphBreak(),
                rdf_shacl_description.TokenParagraphBreak(),
                rdf_shacl_description.TokenText("else")
            ])

        expected = [
            rdf_shacl_description.TokenText("something"),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("else")
        ]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}")

    def test_trailing_breaks(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [
                rdf_shacl_description.TokenText("something"),
                rdf_shacl_description.TokenParagraphBreak(),
                rdf_shacl_description.TokenLineBreak()
            ])

        expected = [rdf_shacl_description.TokenText("something")]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}")

    def test_all_breaks(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [
                rdf_shacl_description.TokenParagraphBreak(),
                rdf_shacl_description.TokenLineBreak()
            ])

        expected = []

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}")

    def test_regression_on_skipped_tokens(self)->None:
        # This is an actual bug that caused unexpected cut-off of the tokens.
        tokens = [
            rdf_shacl_description.TokenText('An element that is referable by its '), 
            rdf_shacl_description.TokenText("'idShort'"), 
            rdf_shacl_description.TokenText('.'), 
            rdf_shacl_description.TokenParagraphBreak(), 
            rdf_shacl_description.TokenText('Something.'),
            rdf_shacl_description.TokenParagraphBreak()
        ]

        got = rdf_shacl_description.without_redundant_breaks(tokens)

        expected = [
            rdf_shacl_description.TokenText('An element that is referable by its '),
            rdf_shacl_description.TokenText("'idShort'"),
            rdf_shacl_description.TokenText('.'),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText('Something.'),
        ]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}")

if __name__ == "__main__":
    unittest.main()
