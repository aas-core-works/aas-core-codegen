import io
import os
import pathlib
import unittest

from aas_core_csharp_codegen import main


class Test_against_recorded(unittest.TestCase):
    # Set this variable to True if you want to re-record the test data,
    # without any checks
    RERECORD = True  # TODO: undo

    def test_on_meta_models(self) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        models_dir = repo_dir / "test_data/meta_models"

        assert models_dir.exists(), f"{models_dir=}"
        assert models_dir.is_dir(), f"{models_dir=}"

        for model_dir in models_dir.iterdir():
            assert model_dir.is_dir(), f"{model_dir}"

            model_pth = model_dir / "meta_model.py"
            assert model_pth.exists() and model_pth.is_file(), model_pth

            expected_dir = (
                    repo_dir / "test_data/csharp/test_end_to_end" / model_dir.name)

            if Test_against_recorded.RERECORD:
                expected_dir.mkdir(exist_ok=True, parents=True)
            else:
                assert expected_dir.exists() and expected_dir.is_dir(), expected_dir

            params = main.Parameters(model_path=model_pth, output_dir=expected_dir)

            stdout = io.StringIO()
            stderr = io.StringIO()

            return_code = main.run(params=params, stdout=stdout, stderr=stderr)

            self.assertEqual(
                "", stderr.getvalue(), "Expected no stderr on valid models")

            self.assertEqual(0, return_code, "Expected 0 return code on valid models")

            stdout_pth = expected_dir / "stdout.txt"
            if Test_against_recorded.RERECORD:
                stdout_pth.write_text(stdout.getvalue())
            else:
                self.assertEqual(stdout.getvalue(), stdout_pth.read_text(), stdout_pth)

            # TODO: check the structure path
            # TODO: check the generated files


if __name__ == "__main__":
    unittest.main()
