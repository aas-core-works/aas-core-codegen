import contextlib
import io
import os
import pathlib
import tempfile
import unittest

import aas_core_csharp_codegen.jsonschema.main


class Test_against_recorded(unittest.TestCase):
    # Set this variable to True if you want to re-record the test data,
    # without any checks
    RERECORD = True  # TODO: undo

    def test_cases(self) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        parent_case_dir = repo_dir / "test_data" / "test_rdf_shacl" / "test_main"
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        for case_dir in parent_case_dir.iterdir():
            assert case_dir.is_dir(), case_dir

            model_pth = case_dir / "input/meta_model.py"
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
                            expected_output_dir.exists()
                            and expected_output_dir.is_dir()
                    ), expected_output_dir

                    tmp_dir = tempfile.TemporaryDirectory()
                    exit_stack.push(tmp_dir)
                    output_dir = pathlib.Path(tmp_dir.name)

                params = aas_core_csharp_codegen.jsonschema.main.Parameters(
                    model_path=model_pth,
                    snippets_dir=snippets_dir,
                    output_dir=output_dir)

                stdout = io.StringIO()
                stderr = io.StringIO()

                return_code = aas_core_csharp_codegen.jsonschema.main.run(
                    params=params, stdout=stdout, stderr=stderr)

                self.assertEqual(
                    "", stderr.getvalue(), "Expected no stderr on valid models")

                self.assertEqual(
                    0, return_code, "Expected 0 return code on valid models")

                stdout_pth = expected_output_dir / "stdout.txt"
                normalized_stdout = stdout.getvalue().replace(
                    str(output_dir), '<output dir>')

                if Test_against_recorded.RERECORD:
                    stdout_pth.write_text(normalized_stdout)
                else:
                    self.assertEqual(
                        normalized_stdout, stdout_pth.read_text(), stdout_pth)

                for relevant_rel_pth in [
                    pathlib.Path('rdf-ontology.ttl'),
                    pathlib.Path('shacl-schema.ttl')
                ]:
                    expected_pth = expected_output_dir / relevant_rel_pth
                    output_pth = output_dir / relevant_rel_pth

                    if not output_pth.exists():
                        raise FileNotFoundError(
                            f"The output file is missing: {output_pth}")

                    if Test_against_recorded.RERECORD:
                        expected_pth.write_text(output_pth.read_text())
                    else:
                        self.assertEqual(
                            expected_pth.read_text(),
                            output_pth.read_text(),
                            f"The files {expected_pth} and {output_pth} do not match.")


if __name__ == "__main__":
    unittest.main()
