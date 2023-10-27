import contextlib
import pathlib
import tempfile
import unittest
import io

import aas_core_meta.v3

from aas_core_codegen.main import Parameters, Target, execute

import tests.common
from tests.rdf_shacl.test_main import REPO_DIR


class Test_jsonld_context(unittest.TestCase):
    def test_jsonld_context_generation(self) -> None:
        expected_jsonld_context_file = (
            REPO_DIR / "test_data" / "jsonld_context" / "context.jsonld"
        )
        expected_jsonld_context = expected_jsonld_context_file.read_text()

        test_case = REPO_DIR / "test_data" / "jsonld_context"

        for module in [aas_core_meta.v3]:
            case_dir = test_case / module.__name__
            expected_output_dir = case_dir / "output"
            assert (
                module.__file__ is not None
            ), f"Expected the module {module!r} to have a __file__, but it has None"
            model_pth = pathlib.Path(module.__file__)
            assert model_pth.exists() and model_pth.is_file(), model_pth
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

                params = Parameters(
                    model_path=model_pth,
                    target=Target.JSONLD_CONTEXT,
                    snippets_dir=case_dir,
                    output_dir=output_dir,
                )

                stdout = io.StringIO()
                stderr = io.StringIO()
                return_code = execute(params=params, stdout=stdout, stderr=stderr)
                if stderr.getvalue() != "":
                    raise AssertionError(
                        f"Expected no stderr on valid models, but got:\n"
                        f"{stderr.getvalue()}"
                    )

                self.assertEqual(
                    0, return_code, "Expected 0 return code on valid models"
                )
                generated_jsonld_context = (output_dir / "context.jsonld").read_text()

                breakpoint()
                self.assertEqual(generated_jsonld_context, expected_jsonld_context)


if __name__ == "__main__":
    unittest.main()
