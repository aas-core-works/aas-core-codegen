# pylint: disable=missing-docstring

import contextlib
import io
import os
import pathlib
import tempfile
import unittest

import aas_core_meta.v3rc2

import aas_core_codegen.main


class Test_against_recorded(unittest.TestCase):
    RERECORD = os.environ.get("AAS_CORE_CODEGEN_RERECORD", "").lower() in (
        "1",
        "true",
        "on",
    )

    def test_cases(self) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        parent_case_dir = repo_dir / "test_data" / "csharp" / "test_main"
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        for module in [aas_core_meta.v3rc2]:
            case_dir = parent_case_dir / module.__name__
            assert case_dir.is_dir(), case_dir

            assert (
                module.__file__ is not None
            ), f"Expected the module {module!r} to have a __file__, but it has None"
            model_pth = pathlib.Path(module.__file__)
            assert model_pth.exists() and model_pth.is_file(), model_pth

            snippets_dir = case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            expected_output_dir = case_dir / "expected_output"

            with contextlib.ExitStack() as exit_stack:
                if Test_against_recorded.RERECORD:
                    output_dir = expected_output_dir
                    expected_output_dir.mkdir(exist_ok=True, parents=True)
                else:
                    assert (
                        expected_output_dir.exists() and expected_output_dir.is_dir()
                    ), expected_output_dir

                    tmp_dir = (
                        tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
                    )
                    exit_stack.push(tmp_dir)
                    output_dir = pathlib.Path(tmp_dir.name)

                params = aas_core_codegen.main.Parameters(
                    model_path=model_pth,
                    target=aas_core_codegen.main.Target.CSHARP,
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

                if Test_against_recorded.RERECORD:
                    stdout_pth.write_text(normalized_stdout, encoding="utf-8")
                else:
                    self.assertEqual(
                        normalized_stdout,
                        stdout_pth.read_text(encoding="utf-8"),
                        stdout_pth,
                    )

                # BEFORE-RELEASE (mristin, 2021-12-13):
                #  check the remainder of the generated files
                for relevant_rel_pth in [
                    pathlib.Path("types.cs"),
                    pathlib.Path("visitation.cs"),
                    pathlib.Path("verification.cs"),
                    pathlib.Path("reporting.cs"),
                    pathlib.Path("stringification.cs"),
                    pathlib.Path("jsonization.cs"),
                    pathlib.Path("xmlization.cs"),
                ]:
                    expected_pth = expected_output_dir / relevant_rel_pth
                    output_pth = output_dir / relevant_rel_pth

                    if not output_pth.exists():
                        raise FileNotFoundError(
                            f"The output file is missing: {output_pth}"
                        )

                    try:
                        output = output_pth.read_text(encoding="utf-8")
                    except Exception as exception:
                        raise RuntimeError(
                            f"Failed to read the output from {output_pth}"
                        ) from exception

                    if Test_against_recorded.RERECORD:
                        expected_pth.write_text(output, encoding="utf-8")
                    else:
                        try:
                            expected_output = expected_pth.read_text(encoding="utf-8")
                        except Exception as exception:
                            raise RuntimeError(
                                f"Failed to read the expected output "
                                f"from {expected_pth}"
                            ) from exception

                        self.assertEqual(
                            expected_output,
                            output,
                            f"The files {expected_pth} and {output_pth} do not match.",
                        )


if __name__ == "__main__":
    unittest.main()
