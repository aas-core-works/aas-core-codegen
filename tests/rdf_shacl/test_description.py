# pylint: disable=missing-docstring

import textwrap
import unittest
from typing import Sequence, List

import tests.description

from aas_core_codegen.rdf_shacl import _description as rdf_shacl_description


def tokens_are_equal(
    that: Sequence[rdf_shacl_description.Token],
    other: Sequence[rdf_shacl_description.Token],
) -> bool:
    if len(that) != len(other):
        return False

    for me, you in zip(that, other):
        if type(me) != type(you):  # pylint: disable=unidiomatic-typecheck
            return False

        if isinstance(me, rdf_shacl_description.TokenText):
            assert isinstance(you, rdf_shacl_description.TokenText)
            if me.content != you.content:
                return False

    return True


class Test_renderer(unittest.TestCase):
    def test_bullet_list(self) -> None:
        text = textwrap.dedent(
            """\
            Some bullets:

            * Test
              me
            * Well
            """
        )
        doc = tests.description.parse_restructured_text(text)

        renderer = rdf_shacl_description.Renderer()
        got, error = renderer.transform(element=doc)
        assert error is None, f"{error}="
        assert got is not None

        expected = [
            rdf_shacl_description.TokenText("Some bullets:"),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("* "),
            rdf_shacl_description.TokenText("Test me"),
            rdf_shacl_description.TokenLineBreak(),
            rdf_shacl_description.TokenText("* "),
            rdf_shacl_description.TokenText("Well"),
        ]
        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )

    def test_two_consecutive_notes(self) -> None:
        text = textwrap.dedent(
            """\
            Some text.

            .. note::

                A single paragraph in the note.

            .. note::

                Another note.

                Yet another paragraph.

            Paragraph at root.
            """
        )

        doc = tests.description.parse_restructured_text(text)
        renderer = rdf_shacl_description.Renderer()
        got, error = renderer.transform(element=doc)

        assert error is None, f"{error}="
        assert got is not None

        expected = [
            rdf_shacl_description.TokenText("Some text."),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("NOTE:"),
            rdf_shacl_description.TokenLineBreak(),
            rdf_shacl_description.TokenText("A single paragraph in the note."),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("NOTE:"),
            rdf_shacl_description.TokenLineBreak(),
            rdf_shacl_description.TokenText("Another note."),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("Yet another paragraph."),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("Paragraph at root."),
        ]
        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )


class Test_without_redundant_breaks(unittest.TestCase):
    def test_empty(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks([])
        expected = []  # type: List[rdf_shacl_description.Token]
        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )

    def test_text(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [rdf_shacl_description.TokenText("something")]
        )

        expected = [rdf_shacl_description.TokenText("something")]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )

    def test_consecutive_line_breaks(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [
                rdf_shacl_description.TokenText("something"),
                rdf_shacl_description.TokenLineBreak(),
                rdf_shacl_description.TokenLineBreak(),
                rdf_shacl_description.TokenText("else"),
            ]
        )

        expected = [
            rdf_shacl_description.TokenText("something"),
            rdf_shacl_description.TokenLineBreak(),
            rdf_shacl_description.TokenText("else"),
        ]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )

    def test_consecutive_paragraph_breaks(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [
                rdf_shacl_description.TokenText("something"),
                rdf_shacl_description.TokenParagraphBreak(),
                rdf_shacl_description.TokenParagraphBreak(),
                rdf_shacl_description.TokenText("else"),
            ]
        )

        expected = [
            rdf_shacl_description.TokenText("something"),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("else"),
        ]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )

    def test_trailing_breaks(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [
                rdf_shacl_description.TokenText("something"),
                rdf_shacl_description.TokenParagraphBreak(),
                rdf_shacl_description.TokenLineBreak(),
            ]
        )

        expected = [rdf_shacl_description.TokenText("something")]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )

    def test_all_breaks(self) -> None:
        got = rdf_shacl_description.without_redundant_breaks(
            [
                rdf_shacl_description.TokenParagraphBreak(),
                rdf_shacl_description.TokenLineBreak(),
            ]
        )

        expected = []  # type: List[rdf_shacl_description.Token]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )

    def test_regression_on_skipped_tokens(self) -> None:
        # This is an actual bug that caused unexpected cut-off of the tokens.
        tokens = [
            rdf_shacl_description.TokenText("An element that is referable by its "),
            rdf_shacl_description.TokenText("'idShort'"),
            rdf_shacl_description.TokenText("."),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("Something."),
            rdf_shacl_description.TokenParagraphBreak(),
        ]  # type: List[rdf_shacl_description.TokenUnion]

        got = rdf_shacl_description.without_redundant_breaks(tokens)

        expected = [
            rdf_shacl_description.TokenText("An element that is referable by its "),
            rdf_shacl_description.TokenText("'idShort'"),
            rdf_shacl_description.TokenText("."),
            rdf_shacl_description.TokenParagraphBreak(),
            rdf_shacl_description.TokenText("Something."),
        ]

        self.assertTrue(
            tokens_are_equal(expected, got), f"Expected {expected!r}, got {got!r}"
        )


if __name__ == "__main__":
    unittest.main()
