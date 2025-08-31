"""Test end-to-end: generate the SDK and then apply it on concrete models."""

import argparse
import io
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
from typing import Final, Sequence, Iterator, Tuple

import aas_core_codegen.main


class IntegrationTestCase:
    """
    Provide a protocol for running different stages of an integration test.

    It is expected that the code of the SDK has been previously generated.

    There are two stages of an integration test:
    * ``build`` — where the project files, including test drivers, are built, and
    * ``execute`` — where the test driver is executed.
    """

    name: Final[str]
    meta_model_path: Final[pathlib.Path]
    input_dir: Final[pathlib.Path]
    output_dir: Final[pathlib.Path]
    test_data_dir: Final[pathlib.Path]

    def __init__(
        self,
        name: str,
        meta_model_path: pathlib.Path,
        input_dir: pathlib.Path,
        output_dir: pathlib.Path,
        test_data_dir: pathlib.Path,
    ) -> None:
        self.name = name
        self.meta_model_path = meta_model_path
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.test_data_dir = test_data_dir

    def _info(self, message: str) -> None:
        """Log the ``message`` to STDOUT."""
        print(f"[{self.name}] {message}")

    def _panic(self, message: str) -> None:
        """Log the ``message`` to STDERR and exit the program."""
        print(f"[{self.name}] {message}", file=sys.stderr)
        sys.exit(1)

    def _generate(
        self,
        meta_model_path: pathlib.Path,
        target: aas_core_codegen.main.Target,
        target_dir: pathlib.Path,
    ) -> None:
        """
        Generate the SDK.

        This method is expected to be called from within the :py:meth:`setup`.
        """
        params = aas_core_codegen.main.Parameters(
            model_path=meta_model_path,
            target=target,
            snippets_dir=self.input_dir / "snippets",
            # NOTE (mristin):
            # The output directory for aas-core-codegen is where we put the SDK code.
            # The SDK code might not necessarily live at the root of the test driver
            # directory, so we call it here ``target_dir``.
            output_dir=target_dir,
        )

        stdout = io.StringIO()
        stderr = io.StringIO()

        return_code = aas_core_codegen.main.execute(
            params=params, stdout=stdout, stderr=stderr
        )
        if stderr.getvalue() != "":
            self._panic(
                f"Expected no stderr when generating the SDK, "
                f"but got:\n{stderr.getvalue()}"
            )
        if return_code != 0:
            self._panic(
                f"Expected 0 return code when generating the SDK, "
                f"but got: {return_code}"
            )

    def setup(self) -> None:
        """Generate the SDK, copy the boilerplate code and set up the test project."""
        return

    def build(self) -> None:
        """
        Build the test project to be executed in the integration test.

        The default is to build nothing — override this method to specify how to build
        the test project.
        """
        return

    def _must_call(self, command: Sequence[str], cwd: pathlib.Path) -> None:
        """Log the command, execute it and panic if it fails."""
        assert all(
            isinstance(part, str) for part in command
        ), f"Expected all parts of the command to be string, but got command: {command}"

        cmd_joined = " ".join(shlex.quote(part) for part in command)
        self._info(f"Executing: {cmd_joined}")
        return_code = subprocess.call(command, cwd=str(cwd))

        if return_code != 0:
            self._panic(
                f"The command {cmd_joined} failed with return code {return_code}"
            )

    def execute(self) -> None:
        """
        Execute the test driver.

        The default is to execute nothing — override this method to call
        your specific test driver.
        """
        return


def _escaped_and_joined_command(command: Sequence[str]) -> str:
    """Generate the string such that it can be copy/pasted into a terminal."""
    return " ".join(shlex.quote(part) for part in command)


class JsonSchemaIntegrationTest(IntegrationTestCase):
    """Test the generation of JSON schema and validate it against the test data."""

    def setup(self) -> None:
        self._generate(
            meta_model_path=self.meta_model_path,
            target=aas_core_codegen.main.Target.JSONSCHEMA,
            target_dir=self.output_dir,
        )

        shutil.copy(
            str(self.input_dir / "boilerplate" / "main.py"), self.output_dir / "main.py"
        )

    def execute(self) -> None:
        self._must_call(
            command=[
                sys.executable,
                str(self.output_dir / "main.py"),
                "--schema_path",
                str(self.output_dir / "schema.json"),
                "--model_path",
                str(self.test_data_dir / "json" / "full.json"),
            ],
            cwd=self.output_dir,
        )


def _over_model_paths(test_data_dir: pathlib.Path) -> Iterator[pathlib.Path]:
    """Iterate over all the possible model files in the given test data directory."""
    for path in test_data_dir.glob("**/*"):
        if path.suffix.lower() in (".xml", ".json"):
            yield path


class PythonIntegrationTest(IntegrationTestCase):
    def setup(self) -> None:
        self._generate(
            meta_model_path=self.meta_model_path,
            target=aas_core_codegen.main.Target.PYTHON,
            target_dir=self.output_dir / "sdk",
        )

        shutil.copy(
            str(self.input_dir / "boilerplate" / "main.py"), self.output_dir / "main.py"
        )

    def execute(self) -> None:
        for model_path in _over_model_paths(self.test_data_dir):
            self._must_call(
                command=[
                    sys.executable,
                    str(self.output_dir / "main.py"),
                    "--model_path",
                    str(model_path),
                ],
                cwd=self.output_dir,
            )


def main() -> None:
    """Execute the main routine."""
    repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent
    integration_tests_dir = repo_dir / "integration_tests"

    meta_model_path = integration_tests_dir / "input" / "meta_model.py"
    test_data_dir = integration_tests_dir / "test_data"

    test_names_to_tests = {
        "jsonschema": JsonSchemaIntegrationTest(
            name="jsonschema",
            meta_model_path=meta_model_path,
            input_dir=integration_tests_dir / "input" / "jsonschema",
            output_dir=integration_tests_dir / "output" / "jsonschema",
            test_data_dir=test_data_dir,
        ),
        "python": PythonIntegrationTest(
            name="python",
            meta_model_path=meta_model_path,
            input_dir=integration_tests_dir / "input" / "python",
            output_dir=integration_tests_dir / "output" / "python",
            test_data_dir=test_data_dir,
        ),
    }

    # NOTE (mristin):
    # We enforce this convention in order to avoid the confusion on the side of
    # the user.
    assert all(
        test_name == test.name for test_name, test in test_names_to_tests.items()
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--test",
        choices=sorted(test_names_to_tests.keys()),
        default=None,
        help="Run only a specific integration test",
    )
    args = parser.parse_args()

    selected_test_names_tests: Sequence[Tuple[str, IntegrationTestCase]]

    if args.test is not None:
        selected_test_names_tests = [(args.test, test_names_to_tests[args.test])]
    else:
        selected_test_names_tests = [
            (test_name, test_names_to_tests[test_name])
            for test_name in sorted(test_names_to_tests.keys())
        ]

    for test_name, test in selected_test_names_tests:
        print(f"Running the test case: {test_name} ...")

        test.setup()
        test.build()
        test.execute()


if __name__ == "__main__":
    main()
