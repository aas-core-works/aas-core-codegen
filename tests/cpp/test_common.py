import unittest

from aas_core_codegen.cpp import common as cpp_common


class TestBreakTypeInLines(unittest.TestCase):
    def test_empty(self) -> None:
        result = cpp_common.break_type_in_lines("")
        self.assertEqual(result, "")

    def test_no_breaks(self) -> None:
        result = cpp_common.break_type_in_lines("const int")
        self.assertEqual(result, "const int")

    def test_breaks(self) -> None:
        result = cpp_common.break_type_in_lines(
            "std::optional<std::vector<std::shared_ptr<IEmbeddedDataSpecification> > >&"
        )
        self.assertEqual(
            result,
            f"""\
std::optional<
  std::vector<
    std::shared_ptr<
      IEmbeddedDataSpecification > > >&""",
        )


if __name__ == "__main__":
    unittest.main()
