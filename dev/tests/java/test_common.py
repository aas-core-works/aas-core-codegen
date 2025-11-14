# pylint: disable=missing-docstring

import unittest

import aas_core_codegen.java.common as java_common


class TestStringLiteral(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual('""', java_common.string_literal(""))

    def test_no_quotes(self) -> None:
        self.assertEqual('"x"', java_common.string_literal("x"))

    def test_tab(self) -> None:
        self.assertEqual('"a\\tb"', java_common.string_literal("a\tb"))


if __name__ == "__main__":
    unittest.main()
