# pylint: disable=missing-docstring

import contextlib
import io
import os
import pathlib
import tempfile
import unittest

import aas_core_meta.v3

import aas_core_codegen.main

import tests.common

REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent


class Test_against_recorded(unittest.TestCase):
    def test_against_expected_meta_models(self) -> None:
        parent_case_dir = (
            REPO_DIR / "test_data" / "rdf_shacl" / "test_main" / "expected"
        )
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        # fmt: off
        test_cases = (
            tests.common.find_meta_models_in_parent_directory_of_test_cases_and_modules(
                parent_case_dir=parent_case_dir,
                aas_core_meta_modules=[aas_core_meta.v3]
            )
        )
        # fmt: on

        for test_case in test_cases:
            snippets_dir = test_case.case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            expected_output_dir = test_case.case_dir / "expected_output"

            with contextlib.ExitStack() as exit_stack:
                if tests.common.RERECORD:
                    output_dir = expected_output_dir
                    expected_output_dir.mkdir(exist_ok=True, parents=True)
                else:
                    assert (
                        expected_output_dir.exists() and expected_output_dir.is_dir()
                    ), expected_output_dir

                    # pylint: disable=consider-using-with
                    tmp_dir = tempfile.TemporaryDirectory()
                    exit_stack.push(tmp_dir)
                    output_dir = pathlib.Path(tmp_dir.name)

                params = aas_core_codegen.main.Parameters(
                    model_path=test_case.model_path,
                    target=aas_core_codegen.main.Target.RDF_SHACL,
                    snippets_dir=snippets_dir,
                    output_dir=output_dir,
                )

                stdout = io.StringIO()
                stderr = io.StringIO()

                return_code = aas_core_codegen.main.execute(
                    params=params, stdout=stdout, stderr=stderr
                )

                if stderr.getvalue() != "":
                    raise AssertionError(
                        f"Expected no stderr on valid models, but got:\n"
                        f"{stderr.getvalue()}"
                    )

                self.assertEqual(
                    0, return_code, "Expected 0 return code on valid models"
                )

                stdout_pth = expected_output_dir / "stdout.txt"
                normalized_stdout = stdout.getvalue().replace(
                    str(output_dir), "<output dir>"
                )

                if tests.common.RERECORD:
                    stdout_pth.write_text(normalized_stdout, encoding="utf-8")
                else:
                    self.assertEqual(
                        normalized_stdout,
                        stdout_pth.read_text(encoding="utf-8"),
                        stdout_pth,
                    )

                for relevant_rel_pth in [
                    pathlib.Path("rdf-ontology.ttl"),
                    pathlib.Path("shacl-schema.ttl"),
                ]:
                    expected_pth = expected_output_dir / relevant_rel_pth
                    output_pth = output_dir / relevant_rel_pth

                    if not output_pth.exists():
                        raise FileNotFoundError(
                            f"The output file is missing: {output_pth}"
                        )

                    if tests.common.RERECORD:
                        expected_pth.write_text(
                            data=output_pth.read_text(encoding="utf-8"),
                            encoding="utf-8",
                        )
                    else:
                        self.assertEqual(
                            expected_pth.read_text(encoding="utf-8"),
                            output_pth.read_text(encoding="utf-8"),
                            f"The files {expected_pth} and {output_pth} do not match.",
                        )

    def test_against_unexpected_meta_models(self) -> None:
        parent_case_dir = (
            REPO_DIR / "test_data" / "rdf_shacl" / "test_main" / "unexpected"
        )
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        # fmt: off
        test_cases = (
            tests.common.find_meta_models_in_parent_directory_of_test_cases_and_modules(
                parent_case_dir=parent_case_dir,
                aas_core_meta_modules=[]
            )
        )
        # fmt: on

        for test_case in test_cases:
            snippets_dir = test_case.case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            expected_output_dir = test_case.case_dir / "expected_output"

            with contextlib.ExitStack() as exit_stack:
                if tests.common.RERECORD:
                    output_dir = expected_output_dir
                    expected_output_dir.mkdir(exist_ok=True, parents=True)
                else:
                    assert (
                        expected_output_dir.exists() and expected_output_dir.is_dir()
                    ), expected_output_dir

                    # pylint: disable=consider-using-with
                    tmp_dir = tempfile.TemporaryDirectory()
                    exit_stack.push(tmp_dir)
                    output_dir = pathlib.Path(tmp_dir.name)

                params = aas_core_codegen.main.Parameters(
                    model_path=test_case.model_path,
                    target=aas_core_codegen.main.Target.RDF_SHACL,
                    snippets_dir=snippets_dir,
                    output_dir=output_dir,
                )

                stdout = io.StringIO()
                stderr = io.StringIO()

                return_code = aas_core_codegen.main.execute(
                    params=params, stdout=stdout, stderr=stderr
                )

                if stderr.getvalue() == "":
                    raise AssertionError(
                        f"Expected stderr on unexpected models, but got nothing "
                        f"for the test case {test_case.case_dir}"
                    )

                self.assertNotEqual(
                    0,
                    return_code,
                    f"Expected non-zero return code "
                    f"on the unexpected model {test_case.case_dir}",
                )

                stderr_pth = expected_output_dir / "stderr.txt"
                normalized_stderr = stderr.getvalue().replace(
                    str(REPO_DIR), "<repo dir>"
                )

                if tests.common.RERECORD:
                    stderr_pth.write_text(normalized_stderr, encoding="utf-8")
                else:
                    self.assertEqual(
                        normalized_stderr,
                        stderr_pth.read_text(encoding="utf-8"),
                        stderr_pth,
                    )


if __name__ == "__main__":
    unittest.main()
