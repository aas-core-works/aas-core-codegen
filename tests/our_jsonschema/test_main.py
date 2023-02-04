# pylint: disable=missing-docstring

import contextlib
import io
import json
import os
import pathlib
import tempfile
import unittest
import warnings
from typing import Optional, MutableMapping

import aas_core_meta.v3rc2

import tests.common

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # NOTE (mristin, 2022-04-08):
    # We need to disable warnings. Jsonschema package at the latest version (4.4.0) has
    # a problem with JSON schema draft 2019-09 and crashes with an recursion error,
    # see: https://github.com/python-jsonschema/jsonschema/issues/847.
    #
    # We revert back to jsonschema 3.2.0, which can not handle 2019-09, but still seems
    # to validate correctly our examples.
    import jsonschema

import aas_core_codegen.main


class Test_against_recorded(unittest.TestCase):
    _REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent
    PARENT_CASE_DIR = _REPO_DIR / "test_data" / "jsonschema" / "test_main"

    def test_against_meta_models(self) -> None:
        assert (
            Test_against_recorded.PARENT_CASE_DIR.exists()
            and Test_against_recorded.PARENT_CASE_DIR.is_dir()
        ), f"{Test_against_recorded.PARENT_CASE_DIR=}"

        # NOTE (mristin, 2023-02-04):
        # We have two sources of metamodels. The main metamodels come from
        # aas-core-meta package. For regression tests or more localized tests, we want
        # to test against much smaller metamodels which are stored locally, as the test
        # data.
        #
        # We resolve the metamodel source like the following. We first check for each
        # test case directory if the file ``meta_model.py`` exists. If it does not, we
        # look up whether the name of the test case directory corresponds to a module
        # name from aas-core-meta.

        modules = [aas_core_meta.v3rc2]

        module_name_to_path = dict()  # type: MutableMapping[str, pathlib.Path]
        for module in modules:
            assert (
                module.__file__ is not None
            ), f"Expected module {module} to have the ``__file__`` attribute set."
            module_name_to_path[module.__name__] = pathlib.Path(module.__file__)

        for case_dir in sorted(
            pth
            for pth in Test_against_recorded.PARENT_CASE_DIR.iterdir()
            if pth.is_dir()
        ):
            model_pth = case_dir / "meta_model.py"  # type: Optional[pathlib.Path]
            assert model_pth is not None

            if not model_pth.exists():
                model_pth = module_name_to_path.get(case_dir.name, None)
                if model_pth is None:
                    raise FileNotFoundError(
                        f"We could not resolve the metamodel for the test case "
                        f"{case_dir}. Neither meta_model.py exists in it, nor does "
                        f"it correspond to any module "
                        f"among {[module.__name__ for module in modules]!r}."
                    )

                if not model_pth.exists():
                    raise FileNotFoundError(
                        f"The metamodel corresponding to the test case {case_dir} "
                        f"does not exist: {model_pth}"
                    )

            snippets_dir = case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            expected_output_dir = case_dir / "expected_output"

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
                    model_path=model_pth,
                    target=aas_core_codegen.main.Target.JSONSCHEMA,
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

                # BEFORE-RELEASE (mristin, 2021-12-13):
                #  check the remainder of the generated files
                for relevant_rel_pth in [
                    pathlib.Path("schema.json"),
                ]:
                    expected_pth = expected_output_dir / relevant_rel_pth
                    output_pth = output_dir / relevant_rel_pth

                    if not output_pth.exists():
                        raise FileNotFoundError(
                            f"The output file is missing: {output_pth}"
                        )

                    if tests.common.RERECORD:
                        expected_pth.write_text(
                            output_pth.read_text(encoding="utf-8"), encoding="utf-8"
                        )
                    else:
                        self.assertEqual(
                            expected_pth.read_text(encoding="utf-8"),
                            output_pth.read_text(encoding="utf-8"),
                            f"The files {expected_pth} and {output_pth} do not match.",
                        )

    def test_on_examples(self) -> None:  # pylint: disable=no-self-use
        assert (
            Test_against_recorded.PARENT_CASE_DIR.exists()
            and Test_against_recorded.PARENT_CASE_DIR.is_dir()
        ), f"{Test_against_recorded.PARENT_CASE_DIR=}"

        for case_dir in Test_against_recorded.PARENT_CASE_DIR.iterdir():
            assert case_dir.is_dir(), case_dir

            schema_pth = case_dir / "expected_output" / "schema.json"

            with schema_pth.open("rt", encoding="utf-8") as fid:
                schema = json.load(fid)

            for data_pth in sorted(
                (case_dir / "examples" / "expected").glob("**/*.json")
            ):
                with data_pth.open("rt", encoding="utf-8") as fid:
                    instance = json.load(fid)

                try:
                    jsonschema.validate(instance=instance, schema=schema)
                except jsonschema.ValidationError as err:
                    raise AssertionError(
                        f"Failed to validate {data_pth} against {schema_pth}"
                    ) from err


if __name__ == "__main__":
    unittest.main()
