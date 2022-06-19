# pylint: disable=missing-docstring
import os
import pathlib
import unittest

from aas_core_codegen import intermediate
from aas_core_codegen.common import LinenoColumner, Error
from aas_core_codegen.csharp import (
    common as csharp_common,
    structure as csharp_structure,
)
from aas_core_codegen import parse

import tests.common


class Test_generation_against_recorded(unittest.TestCase):
    def test_cases(self) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        parent_case_dir = repo_dir / "test_data/csharp/test_structure"
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

            verified_symbol_table, errors = csharp_structure.verify(
                symbol_table=ir_symbol_table
            )
            if errors is not None:
                joined_error = Error(
                    None, "Generating verification code failed", errors
                )
                raise AssertionError(
                    f"Unexpected errors when verifying "
                    f"{model_pth}: {lineno_columner.error_message(joined_error)}"
                )
            assert verified_symbol_table is not None

            code, errors = csharp_structure.generate(
                symbol_table=verified_symbol_table,
                namespace=csharp_common.NamespaceIdentifier("dummyNamespace"),
                spec_impls=dict(),
            )
            if errors is not None:
                joined_error = Error(None, "Generating structure code failed", errors)
                raise AssertionError(
                    f"Unexpected errors in generating structure code "
                    f"for {model_pth}: {lineno_columner.error_message(joined_error)}"
                )
            assert code is not None

            expected_pth = model_pth.parent / "expected_types.cs"
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
