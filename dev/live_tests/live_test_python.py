"""Run integration tests on the Python generated code."""

import argparse
import contextlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Pattern

from aas_core_codegen.common import Stripped
from live_tests import common as live_tests_common


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output_dir",
        help=(
            "Path to where all the assembled project data including the test data "
            "should be copied to. If not specified, everything will be put into "
            "a temporary directory and deleted after the test."
        ),
    )
    parser.add_argument(
        "--select",
        help="Run only the test cases which match the regular expression",
        type=str,
    )
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir) if args.output_dir is not None else None

    select_text = str(args.select) if args.select is not None else None

    select: Optional[Pattern[str]] = None
    if select_text is not None:
        try:
            select = re.compile(select_text)
        except Exception as exception:
            print(f"Problems with --select {select_text}: {exception}", file=sys.stderr)
            return 1

    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

    main_python_expected_dir = (
        repo_root / "dev" / "test_data" / "main" / "python" / "expected"
    )

    assert main_python_expected_dir.exists() and main_python_expected_dir.is_dir()

    live_tests_python_dir = repo_root / "dev" / "test_data" / "live_tests" / "golang"
    assert (
        live_tests_python_dir.exists() and live_tests_python_dir.is_dir()
    ), live_tests_python_dir

    with contextlib.ExitStack() as exit_stack:
        # pylint: disable=consider-using-with

        if output_dir is None:
            temp_dir = tempfile.TemporaryDirectory()
            exit_stack.push(temp_dir)
            output_dir = pathlib.Path(temp_dir.name)
        else:
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exception:
                print(
                    f"Problems with --output_dir {output_dir}: {exception}",
                    file=sys.stderr,
                )
                return 1

        for case_dir in sorted(
            path for path in main_python_expected_dir.iterdir() if path.is_dir()
        ):
            if select is not None and select.match(case_dir.name) is None:
                print(f"Skipping {case_dir.name} since not selected.")
                continue

            print(f"Running the live test on {case_dir.name} ...")

            project_dir = output_dir / case_dir.name
            project_dir.mkdir(exist_ok=True)

            qualified_module_name = Stripped(
                (case_dir / "input" / "snippets" / "qualified_module_name.txt")
                .read_text(encoding="utf-8")
                .strip()
            )

            expected_output_dir = case_dir / "expected_output"

            print(
                f"Copying all the files from {expected_output_dir} to {project_dir} ..."
            )
            for path in sorted(
                path
                for path in expected_output_dir.glob("**/*")
                if path.name != "stdout.txt" and path.is_file()
            ):
                target_path = project_dir / (path.relative_to(expected_output_dir))

                # NOTE (mristin):
                # We check whether there is a change to avoid unnecessary actions
                # due to modification timestamps of the files.

                if not target_path.exists() or target_path.read_text(
                    encoding="utf-8"
                ) != path.read_text(encoding="utf-8"):
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(path, target_path)

            project_name = qualified_module_name.replace("_", "-")

            (project_dir / "pyproject.toml").write_text(
                f"""\
[build-system]
requires = ["setuptools", "setuptools-scm"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.0.1"
requires-python = ">=3.9"

[tool.setuptools.packages.find]
include = ["{qualified_module_name}"]
exclude = ["dev"]

[tool.setuptools.package-data]
"{qualified_module_name}" = ["py.typed"]
""",
                encoding="utf-8",
            )

            (project_dir / "dev" / "pyproject.toml").write_text(
                f"""\
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}-dev"
version = "0.0.1"
requires-python = ">=3.8"

dependencies = [
    "mypy==0.982",
    "pylint==2.15.4; python_version<'3.11'",
    "pylint==4.0.3; python_version>'3.10'",
]

[tool.setuptools]
packages = [
    "tests"
]

# NOTE (mristin):
# We put the configuration of mypy and pylint in separate files as it is a nightmare
# to configure them with pyproject.toml not living in the current working directory
# which is the repository root.
""",
                encoding="utf-8",
            )

            pylint_rc = project_dir / "dev" / "pylint.rc"

            # pylint: disable=line-too-long
            pylint_rc.write_text(
                """\
[FORMAT]
max-line-length=120

[MESSAGES CONTROL]
disable=too-few-public-methods,len-as-condition,duplicate-code,no-else-raise,no-else-return,too-many-locals,too-many-branches,too-many-nested-blocks,too-many-return-statements,unsubscriptable-object,not-an-iterable,broad-except,too-many-statements,protected-access,unnecessary-pass,too-many-statements,too-many-arguments,no-member,too-many-instance-attributes,too-many-lines,undefined-variable,unnecessary-lambda,assignment-from-none,useless-return,unused-argument,too-many-boolean-expressions,consider-using-f-string,use-dict-literal,invalid-name,no-else-continue,no-else-break,unneeded-not,too-many-public-methods,line-too-long,too-many-ancestors,wrong-import-position,too-many-positional-arguments,wrong-import-order,unused-import,missing-docstring
""",
                encoding="utf-8",
            )
            # pylint: enable=line-too-long

            (project_dir / qualified_module_name / "py.typed").write_text(
                """\
# Marker file for PEP 561. The mypy package uses inline types.
""",
                encoding="utf-8",
            )

            (project_dir / qualified_module_name / "__init__.py").write_text(
                f"# This is {qualified_module_name}!\n", encoding="utf-8"
            )

            venv_dir = project_dir / "venv"

            cmd = [sys.executable, "-m", "venv", str(venv_dir)]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {project_dir}"
            )
            subprocess.check_call(cmd, cwd=project_dir)

            if sys.platform.startswith("win"):
                venv_python = venv_dir / "Scripts" / "python.exe"
            else:
                venv_python = venv_dir / "bin" / "python"

            if not venv_python.exists():
                print(
                    f"Python could not be found in the virtual environment: {venv_python}",
                    file=sys.stderr,
                )
                return 1

            cmd = [str(venv_python), "-m", "pip", "install", "-e", "."]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {project_dir}"
            )
            subprocess.check_call(cmd, cwd=project_dir)

            cmd = [str(venv_python), "-m", "pip", "install", "-e", "dev/"]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {project_dir}"
            )
            subprocess.check_call(cmd, cwd=project_dir)

            cmd = [str(venv_python), "-m", "mypy", "--strict", qualified_module_name]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {project_dir}"
            )
            subprocess.check_call(cmd, cwd=project_dir)

            cmd = [
                str(venv_python),
                "-m",
                "pylint",
                f"--rcfile={pylint_rc.relative_to(project_dir)}",
                qualified_module_name,
            ]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {project_dir}"
            )
            subprocess.check_call(cmd, cwd=project_dir)

            case_test_data_dir = live_tests_python_dir / "test_data" / case_dir.name
            if case_test_data_dir.exists():
                target_test_data = project_dir / "test_data"

                print(
                    f"Copying test data from {case_test_data_dir} "
                    f"to {target_test_data} ..."
                )
                for pth in sorted(case_test_data_dir.glob("**/*")):
                    if not pth.is_file():
                        continue

                    target_pth = target_test_data / pth.relative_to(case_test_data_dir)

                    target_pth.parent.mkdir(exist_ok=True, parents=True)

                    shutil.copy(pth, target_pth)

                print("Running the tests...")

                env_var_prefix = qualified_module_name.replace(".", "_").upper()

                cmd = [
                    str(venv_python),
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "dev/tests",
                ]

                env = os.environ.copy()

                # NOTE (mristin):
                # We remove PYTHONPATH from the environment, or the python in the live
                # test will run with the modules imported from *this* repository as
                # well.
                env.pop("PYTHONPATH", None)

                env_var_test_data_dir = f"{env_var_prefix}_TEST_DATA_DIR"
                env_var_test_record_mode = f"{env_var_prefix}_TESTS_RECORD_MODE"

                env[env_var_test_data_dir] = str(project_dir / "test_data")
                env[env_var_test_record_mode] = "1"

                print(
                    f"Running "
                    f"{env_var_test_data_dir}"
                    f"={env.get(env_var_test_data_dir)} "
                    f"{env_var_test_record_mode}"
                    f"={env.get(env_var_test_record_mode)} "
                    f"{live_tests_common.escape_and_join_command(cmd)} "
                    f"in {project_dir}"
                )
                subprocess.check_call(cmd, cwd=project_dir, env=env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
