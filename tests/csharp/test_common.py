import unittest

from aas_core_csharp_codegen.csharp import structure


class TestStringLiteral(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual('""', structure.string_literal(""))


if __name__ == "__main__":
    unittest.main()
