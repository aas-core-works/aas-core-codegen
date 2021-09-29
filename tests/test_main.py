import contextlib
import io
import os
import pathlib
import tempfile
import unittest

from aas_core_csharp_codegen import main


class Test_against_recorded(unittest.TestCase):
    # Set this variable to True if you want to re-record the test data,
    # without any checks
    RERECORD = True  # TODO: undo

    def test_cases(self) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent

        parent_case_dir = repo_dir / "test_data" / "test_main"
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        for case_dir in parent_case_dir.iterdir():
            assert case_dir.is_dir(), case_dir

            model_pth = case_dir / "input/meta_model.py"
            assert model_pth.exists() and model_pth.is_file(), model_pth

            snippets_dir = case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            namespace = (case_dir / "input/namespace.txt").read_text()

            expected_output_dir = case_dir / "expected_output"

            with contextlib.ExitStack() as exit_stack:
                if Test_against_recorded.RERECORD:
                    output_dir = expected_output_dir
                    expected_output_dir.mkdir(exist_ok=True, parents=True)
                else:
                    assert (
                            expected_output_dir.exists()
                            and expected_output_dir.is_dir()
                    ), expected_output_dir

                    tmp_dir = tempfile.TemporaryDirectory()
                    exit_stack.push(tmp_dir)
                    output_dir = pathlib.Path(tmp_dir.name)

                params = main.Parameters(
                    model_path=model_pth,
                    snippets_dir=snippets_dir,
                    namespace=namespace,
                    output_dir=output_dir)

                stdout = io.StringIO()
                stderr = io.StringIO()

                return_code = main.run(params=params, stdout=stdout, stderr=stderr)

                self.assertEqual(
                    "", stderr.getvalue(), "Expected no stderr on valid models")

                self.assertEqual(
                    0, return_code, "Expected 0 return code on valid models")

                stdout_pth = expected_output_dir / "stdout.txt"
                if Test_against_recorded.RERECORD:
                    stdout_pth.write_text(stdout.getvalue())
                else:
                    self.assertEqual(
                        stdout.getvalue(), stdout_pth.read_text(), stdout_pth)

                self.assertEqual(
                    (expected_output_dir / "types.cs").read_text(),
                    (output_dir / "types.cs").read_text(),
                    expected_output_dir)

                # TODO: check the remainder of the generated files


if __name__ == "__main__":
    unittest.main()
