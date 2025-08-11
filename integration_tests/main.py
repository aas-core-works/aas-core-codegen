import aas_core_codegen.main
import pathlib
import os
import io
import warnings
import json
from typing import List
import shutil
import subprocess
import argparse

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


def copy_dir_contents(src_dir, dst_dir):
    for item in os.listdir(src_dir):
        src_path = os.path.join(src_dir, item)
        dst_path = os.path.join(dst_dir, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)


class IntegrationTestCase:

    target: aas_core_codegen.main.Target
    output_subdir = ""

    def generate(
        self,
        model_path: pathlib.Path,
        input_dir: pathlib.Path,
        output_dir: pathlib.Path,
    ):
        params = aas_core_codegen.main.Parameters(
            model_path=model_path,
            target=self.target,
            snippets_dir=input_dir / "snippets",
            output_dir=output_dir / self.output_subdir,
        )

        stdout = io.StringIO()
        stderr = io.StringIO()

        return_code = aas_core_codegen.main.execute(
            params=params, stdout=stdout, stderr=stderr
        )
        if stderr.getvalue() != "":
            raise AssertionError(
                f"Expected no stderr on valid models, but got:\n" f"{stderr.getvalue()}"
            )
        assert return_code == 0, "Expected 0 return code on valid models"

        additional_dir = input_dir / "additional"
        if additional_dir.exists():
            copy_dir_contents(additional_dir, output_dir)

    def build(self):
        print("Nothing to build.")

    def execute(
        self, is_xml: bool, output_dir: pathlib.Path, test_data_dir: pathlib.Path
    ):
        raise NotImplementedError(self)


class JsonSchemaIntegrationTest(IntegrationTestCase):
    target = aas_core_codegen.main.Target.JSONSCHEMA

    def execute(self, output_dir: pathlib.Path, test_data_dir: pathlib.Path):
        if "xml" in test_data_dir.parts:
            print("XML not supported")
            return
        schema_path = output_dir / "schema.json"
        with open(schema_path) as fd:
            schema = json.load(fd)
        for file in test_data_dir.iterdir():
            with open(file) as fd:
                instance = json.load(fd)
            try:
                jsonschema.validate(instance=instance, schema=schema)
            except jsonschema.ValidationError as err:
                raise AssertionError(
                    f"Failed to validate {file} against {schema_path}"
                ) from err
            print(f"{file}: pass")


class PythonIntegrationTest(IntegrationTestCase):
    target = aas_core_codegen.main.Target.PYTHON
    output_subdir = "aas_core"

    def execute(self, output_dir, test_data_dir):
        subprocess.check_call(["python3", output_dir / "main.py", test_data_dir])

    def execute_xml(self, output_dir, test_data_dir):
        subprocess.check_call(["python3", output_dir / "main.py", test_data_dir])


tests: List[IntegrationTestCase] = [
    JsonSchemaIntegrationTest(),
    PythonIntegrationTest(),
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        type=aas_core_codegen.main.Target,
        choices=list(aas_core_codegen.main.Target),
        default=None,
        help="Run integration test for specific target only",
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        default=False,
        help="Skip code generation",
    )
    args = parser.parse_args()
    print("Running integration tests, this might take a few minutes.")
    print()
    root_dir = pathlib.Path(os.path.realpath(__file__)).parent
    model_path = root_dir / "input" / "model.py"
    if args.target:
        selected_tests = [i for i in tests if i.target == args.target]
    else:
        selected_tests = tests
    for test in selected_tests:
        input_dir = root_dir / "input" / test.target.value
        output_dir = root_dir / "output" / test.target.value
        print(f"Target: {test.target.value}:")
        print("Generating...")
        if args.skip_generation:
            print("Skipped.")
        else:
            test.generate(model_path, input_dir, output_dir)
        print("Building...")
        test.build()
        print("Executing JSON...")
        test.execute(output_dir, root_dir / "test_data" / "json")
        print("Executing XML...")
        test.execute(output_dir, root_dir / "test_data" / "xml")
        print(f"Target {test.target.value} finished without errors.")
        print()
    print(f"{len(selected_tests)} integration tests finished without errors.")
