# pylint: disable=missing-docstring

import unittest

from aas_core_codegen.xsd import main as xsd_main


class Test_undo_escaping_x(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual("", xsd_main._undo_escaping_backslash_x_in_pattern(""))

    def test_no_escaped(self) -> None:
        self.assertEqual(
            "test me", xsd_main._undo_escaping_backslash_x_in_pattern("test me")
        )

    def test_only_escaped(self) -> None:
        self.assertEqual(
            "\xff", xsd_main._undo_escaping_backslash_x_in_pattern("\\xff")
        )

    def test_prefix(self) -> None:
        self.assertEqual(
            "A\xff", xsd_main._undo_escaping_backslash_x_in_pattern("A\\xff")
        )

    def test_suffix(self) -> None:
        self.assertEqual(
            "\xffB", xsd_main._undo_escaping_backslash_x_in_pattern("\\xffB")
        )

    def test_prefix_suffix(self) -> None:
        self.assertEqual(
            "A\xffB", xsd_main._undo_escaping_backslash_x_in_pattern("A\\xffB")
        )

    def test_multiple(self) -> None:
        self.assertEqual(
            "A\xf1B\xf2C",
            xsd_main._undo_escaping_backslash_x_in_pattern("A\\xf1B\\xf2C"),
        )

    def test_complex(self) -> None:
        pattern = (
            "([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+/([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+([ \t]*;"
            "[ \t]*([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+=(([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+|"
            '"(([\t !#-\\[\\]-~]|[\\x80-\\xff])|\\\\([\t !-~]|[\\x80-\\xff]))*"))*'
        )

        expected = (
            "([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+/([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+([ \t]*;"
            "[ \t]*([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+=(([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+|"
            '"(([\t !#-\\[\\]-~]|[\x80-\xff])|\\\\([\t !-~]|[\x80-\xff]))*"))*'
        )

        self.assertEqual(
            expected, xsd_main._undo_escaping_backslash_x_in_pattern(pattern)
        )


class Test_translate_pattern(unittest.TestCase):
    # NOTE (mristin, 2022-06-18):
    # This is relevant since XSD are always anchored.
    # See: https://stackoverflow.com/questions/4367914/regular-expression-in-xml-schema-definition-fails

    def test_table_for_removing_anchors(self) -> None:
        for pattern, expected, identifier in [
            ("^$", "", "empty"),
            ("^something$", "something", "simple_literal"),
            ("(^.*$)", "(.*)", "within_a_group"),
        ]:
            fixed, error = xsd_main._translate_pattern(pattern)
            assert error is None, identifier
            assert fixed is not None, identifier

            self.assertEqual(expected, fixed, identifier)

    def test_table_for_rendering_quantifiers(self) -> None:
        # NOTE (mristin, 2024-03-22):
        # We explicitly test for quantifiers to make sure that they all comply with
        # XSD patterns. For example, when only the maximum quantifier is given,
        # the minimum quantifier of 0 must be indicated explicitly.
        for pattern, expected, identifier in [
            ("a{1}", "a{1}", "exact repetition"),
            ("a{1,}", "a+", "min 1 repetition"),
            ("a{2,}", "a{2,}", "more than 1 min repetition"),
            ("a{,2}", "a{0,2}", "only max repetition"),
            ("a{1,2}", "a{1,2}", "min and max repetition"),
        ]:
            fixed, error = xsd_main._translate_pattern(pattern)
            assert error is None, identifier
            assert fixed is not None, identifier

            self.assertEqual(expected, fixed, identifier)


if __name__ == "__main__":
    unittest.main()
