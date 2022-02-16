# pylint: disable=missing-docstring

import unittest

from aas_core_codegen.rdf_shacl import common as rdf_shacl_common


class Test_string_literal(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual('""', rdf_shacl_common.string_literal(""))

    def test_no_escapes(self) -> None:
        self.assertEqual('"something"', rdf_shacl_common.string_literal("something"))

    def test_escape_single_line(self) -> None:
        self.assertEqual(
            '"some\\"thing"', rdf_shacl_common.string_literal('some"thing')
        )

    def test_multi_line_no_escape(self) -> None:
        self.assertEqual(
            r'"some\nthing"', rdf_shacl_common.string_literal("some\nthing")
        )

    def test_multi_line_escape(self) -> None:
        self.assertEqual(
            r'"some\nthi\"ng"', rdf_shacl_common.string_literal('some\nthi"ng')
        )


if __name__ == "__main__":
    unittest.main()
