# pylint: disable=missing-docstring

import contextlib
import io
import os
import pathlib
import shutil
import tempfile
import unittest

import aas_core_codegen.main

import tests.common


class Test_against_recorded(unittest.TestCase):
    def _run_tests(
            self,
            target: aas_core_codegen.main.Target
    ) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        parent_case_dir = repo_dir / "dev" / "test_data" / "test_main" / target.value

        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        for model_pth in tests.common.REAL_META_MODEL_PATHS:
            case_dir = parent_case_dir / model_pth.stem
            assert case_dir.is_dir(), case_dir

            snippets_dir = case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            expected_output_dir = case_dir / "expected_output"

            with contextlib.ExitStack() as exit_stack:
                if tests.common.RERECORD:
                    output_dir = expected_output_dir

                    # NOTE (mristin):
                    # We add this check to make sure we do not delete anything
                    # important.
                    assert output_dir.name == "expected_output"

                    shutil.rmtree(expected_output_dir, ignore_errors=True)

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
                    model_path=model_pth,
                    target=target,
                    snippets_dir=snippets_dir,
                    output_dir=output_dir,
                    cache_model=tests.common.CACHE_MAIN_MODELS,
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

                normalized_stdout = stdout.getvalue().replace(
                    str(output_dir), "<output dir>"
                )

                if tests.common.RERECORD:
                    stdout_pth = expected_output_dir / "stdout.txt"
                    stdout_pth.write_text(normalized_stdout, encoding="utf-8")

                if not tests.common.RERECORD:
                    tests.common.assert_got_as_expected_output_dir(
                        output_dir=output_dir,
                        expected_output_dir=expected_output_dir,
                        normalized_stdout=normalized_stdout,
                    )

    def test_cpp(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.CPP)

    def test_csharp(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.CSHARP)

    def test_golang(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.GOLANG)

    def test_java(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.JAVA)

    def test_jsonld_context(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.JSONLD_CONTEXT)

    def test_jsonschema(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.JSONSCHEMA)

    def test_opcua(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.OPCUA)

    def test_protobuf(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.PROTOBUF)

    def test_python(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.PYTHON)

    def test_python_protobuf(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.PYTHON_PROTOBUF)

    def test_rdf_shacl(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.RDF_SHACL)

    def test_typescript(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.TYPESCRIPT)

    def test_xsd(self) -> None:
        self._run_tests(target=aas_core_codegen.main.Target.XSD)


if __name__ == "__main__":
    unittest.main()
