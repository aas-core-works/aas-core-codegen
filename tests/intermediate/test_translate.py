import os
import pathlib
import textwrap
import unittest
from typing import List, Tuple

import tests.common
from aas_core_codegen import intermediate
from aas_core_codegen.intermediate import doc as intermediate_doc
from aas_core_codegen.common import Identifier


class Test_in_lining_of_constructor_statements(unittest.TestCase):
    def test_case(self) -> None:
        source = textwrap.dedent(
            """\
            @abstract
            class VeryAbstract:
                some_property: int
            
                @require(lambda some_property: some_property > 0)
                def __init__(self, some_property: int) -> None:
                    self.some_property = some_property
            
            
            @abstract
            class Abstract(VeryAbstract):
                another_property: int
            
                @require(lambda another_property: another_property > 0)
                def __init__(self, some_property: int, another_property: int) -> None:
                    VeryAbstract.__init__(self, some_property)
                    self.another_property = another_property
                    
            class Concrete(Abstract):
                yet_another_property: int
            
                @require(lambda yet_another_property: yet_another_property > 0)
                def __init__(
                        self, 
                        some_property: int, 
                        another_property: int,
                        yet_another_property: int
                ) -> None:
                    Abstract.__init__(self, some_property, another_property)
                    self.yet_another_property = yet_another_property


            class Reference:
                pass
                
            __book_url__ = "dummy"
            __book_version__ = "dummy"
            associate_ref_with(Reference)
            """
        )

        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)

        assert symbol_table is not None

        concrete = symbol_table.must_find(Identifier("Concrete"))
        assert isinstance(concrete, intermediate.Class)

        self.assertEqual(
            ["some_property", "another_property", "yet_another_property"],
            [stmt.name for stmt in concrete.constructor.statements],
        )


class Test_parsing_docstrings(unittest.TestCase):
    def test_class_reference(self) -> None:
        source = textwrap.dedent(
            '''\
            class Some_class:
                """
                This is some documentation.

                 * Nested reference :class:`.Some_class`
                 """
            
            class Reference:
                pass
                
            __book_url__ = "dummy"
            __book_version__ = "dummy"
            associate_ref_with(Reference)
            '''
        )

        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)

        assert symbol_table is not None

        some_class = symbol_table.must_find(Identifier("Some_class"))
        assert isinstance(some_class, intermediate.Class)

        assert some_class.description is not None

        symbol_references = list(
            some_class.description.document.findall(
                condition=intermediate_doc.SymbolReference
            )
        )

        self.assertEqual(1, len(symbol_references))
        self.assertIsInstance(symbol_references[0].symbol, intermediate.Class)


class Test_against_recorded(unittest.TestCase):
    # Set this variable to True if you want to re-record the test data,
    # without any checks
    RERECORD = False

    def test_cases(self) -> None:
        this_dir = pathlib.Path(os.path.realpath(__file__)).parent
        repo_root = this_dir.parent.parent
        test_cases_dir = repo_root / "test_data/intermediate"

        assert test_cases_dir.exists(), f"{test_cases_dir=}"
        assert test_cases_dir.is_dir(), f"{test_cases_dir=}"

        # The expected cases should have no errors.
        expected_pths = sorted((test_cases_dir / "expected").glob("**/meta_model.py"))
        meta_model_pths_expected_errors = [
            (pth, False) for pth in expected_pths
        ]  # type: List[Tuple[pathlib.Path, bool]]

        unexpected_pths = sorted(
            (test_cases_dir / "unexpected").glob("**/meta_model.py")
        )

        meta_model_pths_expected_errors.extend((pth, True) for pth in unexpected_pths)

        for meta_model_pth, expected_errors in meta_model_pths_expected_errors:
            case_dir = meta_model_pth.parent

            try:
                source = meta_model_pth.read_text(encoding="utf-8")
            except Exception as exception:
                raise AssertionError(
                    f"Unexpected exception when reading "
                    f"from {meta_model_pth.relative_to(repo_root)}"
                ) from exception

            try:
                symbol_table, error = tests.common.translate_source_to_intermediate(
                    source=source
                )
            except Exception as exception:
                raise AssertionError(
                    f"Unexpected exception in source-to-intermediate translation "
                    f"for source {meta_model_pth.relative_to(repo_root)}"
                ) from exception

            if not expected_errors and error is not None:
                raise AssertionError(
                    f"Expected no errors in the test "
                    f"case {case_dir.relative_to(test_cases_dir)}, but got:\n"
                    f"{tests.common.most_underlying_messages(error)}"
                )

            elif expected_errors and error is None:
                raise AssertionError(
                    f"Expected errors in the test "
                    f"case {case_dir.relative_to(test_cases_dir)}, but got none."
                )

            else:
                pass

            expected_symbol_table_pth = case_dir / "expected_symbol_table.txt"
            expected_error_pth = case_dir / "expected_error.txt"

            if expected_errors:
                if expected_symbol_table_pth.exists():
                    raise AssertionError(
                        f"Unexpected recorded symbol table file when errors "
                        f"are expected: {expected_symbol_table_pth}"
                    )

                assert error is not None

                error_str = tests.common.most_underlying_messages(error)

                if Test_against_recorded.RERECORD:
                    expected_error_pth.write_text(error_str)
                else:
                    expected_error_str = expected_error_pth.read_text()
                    self.assertEqual(expected_error_str, error_str, f"{case_dir=}")

            else:
                if expected_error_pth.exists():
                    raise AssertionError(
                        f"Unexpected recorded error file when no errors "
                        f"are expected: {expected_error_pth}"
                    )

                assert symbol_table is not None

                symbol_table_str = intermediate.dump(symbol_table)

                if Test_against_recorded.RERECORD:
                    expected_symbol_table_pth.write_text(symbol_table_str)
                else:
                    expected_symbol_table_str = expected_symbol_table_pth.read_text()
                    self.assertEqual(
                        expected_symbol_table_str,
                        symbol_table_str,
                        f"{case_dir=}, {error=}",
                    )


if __name__ == "__main__":
    unittest.main()
