# pylint: disable=missing-docstring
import os
import pathlib
import unittest

from aas_core_codegen import intermediate
from aas_core_codegen.common import LinenoColumner, Error
from aas_core_codegen.csharp import (
    common as csharp_common,
    verification as csharp_verification,
)
from aas_core_codegen import parse

import tests.common


class Test_wrap_invariant_description(unittest.TestCase):
    def test_empty(self) -> None:
        got = csharp_verification._generate._wrap_invariant_description(text="")

        self.assertListEqual([""], got)

    def test_short_word(self) -> None:
        got = csharp_verification._generate._wrap_invariant_description(
            text="something short"
        )

        self.assertListEqual(["something short"], got)

    # noinspection SpellCheckingInspection
    def test_normal_text(self) -> None:
        text = (
            "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, "
            "sed diam nonumy eirmod tempor invidunt ut labore et dolore magna "
            "aliquyam erat, sed diam voluptua. At vero eos et accusam et "
            "justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea "
            "takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit "
            "amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt "
            "ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos "
            "et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, "
            "no sea takimata sanctus est Lorem ipsum dolor sit amet."
        )

        expected = [
            "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, ",
            "sed diam nonumy eirmod tempor invidunt ut labore et dolore ",
            "magna aliquyam erat, sed diam voluptua. At vero eos et ",
            "accusam et justo duo dolores et ea rebum. Stet clita kasd ",
            "gubergren, no sea takimata sanctus est Lorem ipsum dolor ",
            "sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing ",
            "elitr, sed diam nonumy eirmod tempor invidunt ut labore et ",
            "dolore magna aliquyam erat, sed diam voluptua. At vero eos ",
            "et accusam et justo duo dolores et ea rebum. Stet clita ",
            "kasd gubergren, no sea takimata sanctus est Lorem ipsum ",
            "dolor sit amet.",
        ]

        got = csharp_verification._generate._wrap_invariant_description(text=text)
        self.assertListEqual(expected, got)

    def test_very_long_word(self) -> None:
        word = "1234567890" * 90

        text = f"prefix {word} suffix"

        expected = ["prefix ", f"{word} ", "suffix"]

        got = csharp_verification._generate._wrap_invariant_description(text=text)
        self.assertListEqual(expected, got)

    def test_article_kept_on_the_same_line(self) -> None:
        somethings = " ".join(["a something"] * 10)

        text = f"prefix {somethings} suffix"

        expected = [
            "prefix a something a something a something a something ",
            "a something a something a something a something a something ",
            "a something suffix",
        ]

        got = csharp_verification._generate._wrap_invariant_description(text=text)
        self.assertListEqual(expected, got)

    def test_only_articles(self) -> None:
        text = " ".join(["a an the"] * 60)
        expected = [
            "a an the a an the a an the a an the a an the a an the a an ",
            "the a an the a an the a an the a an the a an the a an the a ",
            "an the a an the a an the a an the a an the a an the a an ",
            "the a an the a an the a an the a an the a an the a an the a ",
            "an the a an the a an the a an the a an the a an the a an ",
            "the a an the a an the a an the a an the a an the a an the a ",
            "an the a an the a an the a an the a an the a an the a an ",
            "the a an the a an the a an the a an the a an the a an the a ",
            "an the a an the a an the a an the a an the a an the a an ",
            "the a an the",
        ]

        got = csharp_verification._generate._wrap_invariant_description(text=text)
        self.assertListEqual(expected, got)


class Test_pattern_translation_against_recorded(unittest.TestCase):
    def test_cases(self) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        parent_case_dir = (
            repo_dir / "test_data/csharp/test_verification/pattern_verification"
        )
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        for model_pth in sorted(parent_case_dir.glob("**/model.py")):
            text = model_pth.read_text(encoding="utf-8")
            atok, parse_exception = parse.source_to_atok(source=text)
            assert (
                parse_exception is None
            ), f"Unexpected parse exception in {model_pth}: {parse_exception=}"
            assert atok is not None

            lineno_columner = LinenoColumner(atok=atok)
            parsed_symbol_table, error = parse.atok_to_symbol_table(atok=atok)

            assert error is None, (
                f"Unexpected error in parsing {model_pth}: "
                f"{lineno_columner.error_message(error)}"
            )
            assert parsed_symbol_table is not None

            ir_symbol_table, error = intermediate.translate(
                parsed_symbol_table=parsed_symbol_table,
                atok=atok,
            )

            assert error is None, (
                f"Unexpected error in translating {model_pth} to intermediate: "
                f"{lineno_columner.error_message(error)}"
            )
            assert ir_symbol_table is not None

            code, errors = csharp_verification.generate(
                symbol_table=ir_symbol_table,
                namespace=csharp_common.NamespaceIdentifier("dummyNamespace"),
                spec_impls=dict(),
            )
            if errors is not None:
                joined_error = Error(
                    None, "Generating verification code failed", errors
                )
                raise AssertionError(
                    f"Unexpected errors in generating verification code "
                    f"for {model_pth}: {lineno_columner.error_message(joined_error)}"
                )
            assert code is not None

            expected_pth = model_pth.parent / "expected_verification.cs"
            if tests.common.RERECORD:
                expected_pth.write_text(code, encoding="utf-8")
            else:
                try:
                    expected_code = expected_pth.read_text(encoding="utf-8")
                except Exception as exception:
                    raise RuntimeError(
                        f"Failed to read the expected code " f"from {expected_pth}"
                    ) from exception

                self.assertEqual(expected_code, code)


if __name__ == "__main__":
    unittest.main()
