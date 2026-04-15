"""Run integration tests on the Golang generated code."""

# pylint: disable=wrong-import-position

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

if sys.version_info <= (3, 11):
    import more_itertools as itertools
else:
    import itertools

from aas_core_codegen.common import Stripped
from aas_core_codegen.golang import common as golang_common

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

    # region Find goimports

    # NOTE (mristin):
    # We use goimports to post-process the generated code so that we don't have to
    # fiddle around in the code generator to figure out which imports are used and
    # which can be omitted.
    #
    # Go compiler treats unused imports as errors, so removing unused imports with
    # goimports is strictly necessary.

    goimports_path = shutil.which("goimports")
    alternative_goimports_path = pathlib.Path.home() / "go/bin/goimports"

    if shutil.which("goimports") is None:
        if alternative_goimports_path.exists():
            goimports_path = str(alternative_goimports_path)

    if goimports_path is None:
        path_env_var = os.environ.get("PATH", "")
        print(
            f"goimports could not be found on your PATH "
            f"nor in {alternative_goimports_path} -- have you installed it "
            f"with go install golang.org/x/tools/cmd/goimports@latest ?\n\n"
            f"PATH: {path_env_var}",
            file=sys.stderr,
        )
        return 1

    # endregion

    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

    main_golang_expected_dir = (
        repo_root / "dev" / "test_data" / "main" / "golang" / "expected"
    )

    assert main_golang_expected_dir.exists() and main_golang_expected_dir.is_dir()

    live_tests_golang_dir = repo_root / "dev" / "test_data" / "live_tests" / "golang"
    assert (
        live_tests_golang_dir.exists() and live_tests_golang_dir.is_dir()
    ), live_tests_golang_dir

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
            path for path in main_golang_expected_dir.iterdir() if path.is_dir()
        ):
            if select is not None and select.match(case_dir.name) is None:
                print(f"Skipping {case_dir.name} since not selected.")
                continue

            print(f"Running the live test on {case_dir.name} ...")

            module_dir = output_dir / case_dir.name
            module_dir.mkdir(exist_ok=True)

            repo_url = Stripped(
                (case_dir / "input" / "snippets" / "repo_url.txt")
                .read_text(encoding="utf-8")
                .strip()
            )

            expected_output_dir = case_dir / "expected_output"

            print(
                f"Copying all the files from {expected_output_dir} to {module_dir} ..."
            )
            for path in sorted(
                path
                for path in expected_output_dir.glob("**/*")
                if path.name != "stdout.txt" and path.is_file()
            ):
                target_path = module_dir / (path.relative_to(expected_output_dir))

                # NOTE (mristin):
                # We check whether there is a change to avoid unnecessary recompilations
                # due to modification timestamps of the files.

                if not target_path.exists() or target_path.read_text(
                    encoding="utf-8"
                ) != path.read_text(encoding="utf-8"):
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(path, target_path)

            (module_dir / "go.mod").write_text(
                f"""\
module {repo_url}

go 1.18
""",
                encoding="utf-8",
            )

            for chunk in itertools.batched(sorted(module_dir.glob("**/*.go")), 64):
                cmd = [goimports_path, "-w"] + [
                    str(pth.relative_to(module_dir)) for pth in chunk
                ]
                print(
                    f"Running {live_tests_common.escape_and_join_command(cmd)} "
                    f"in {module_dir}"
                )
                subprocess.check_call(cmd, cwd=module_dir)

            cmd = ["go", "build", "./..."]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {module_dir}"
            )
            subprocess.check_call(cmd, cwd=module_dir)

            case_test_data_dir = live_tests_golang_dir / "test_data" / case_dir.name
            if case_test_data_dir.exists():
                # NOTE (mristin):
                # Go expects the test data in ``testdata`` (no underscore) directory.
                target_test_data = module_dir / "testdata"

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

                env_var_prefix = golang_common.repo_url_to_environment_variable(
                    repo_url
                )

                cmd = ["go", "test", "./..."]
                env = os.environ.copy()

                env_var_test_data_dir = f"{env_var_prefix}_TEST_DATA_DIR"
                env_var_test_record_mode = f"{env_var_prefix}_TEST_RECORD_MODE"

                env[env_var_test_data_dir] = str(module_dir / "testdata")
                env[env_var_test_record_mode] = "1"

                print(
                    f"Running "
                    f"{env_var_test_data_dir}"
                    f"={env.get(env_var_test_data_dir)} "
                    f"{env_var_test_record_mode}"
                    f"={env.get(env_var_test_record_mode)} "
                    f"{live_tests_common.escape_and_join_command(cmd)} "
                    f"in {module_dir}"
                )
                subprocess.check_call(cmd, cwd=module_dir, env=env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
