#!/usr/bin/env python3

"""Run pre-commit checks on the repository."""
import argparse
import difflib
import enum
import os
import pathlib
import shlex
import subprocess
import sys
from typing import Optional, Mapping, Sequence


# pylint: disable=unnecessary-comprehension


class Step(enum.Enum):
    """Enumerate different pre-commit steps."""

    REFORMAT = "reformat"
    MYPY = "mypy"
    PYLINT = "pylint"
    CHECK_TEST_META_MODELS_COINCIDE = "check-test-meta-models-coincide"
    TEST = "test"
    DOCTEST = "doctest"
    CHECK_INIT_AND_SETUP_COINCIDE = "check-init-and-setup-coincide"
    CHECK_HELP_IN_README = "check-help-in-readme"


def call_and_report(
    verb: str,
    cmd: Sequence[str],
    cwd: Optional[pathlib.Path] = None,
    env: Optional[Mapping[str, str]] = None,
) -> int:
    """
    Wrap a subprocess call with the reporting to STDERR if it failed.

    Return 1 if there is an error and 0 otherwise.
    """
    exit_code = subprocess.call(cmd, cwd=str(cwd) if cwd is not None else None, env=env)

    if exit_code != 0:
        cmd_str = " ".join(shlex.quote(part) for part in cmd)
        print(
            f"Failed to {verb} with exit code {exit_code}: {cmd_str}", file=sys.stderr
        )

    return exit_code


def main() -> int:
    """Execute entry_point routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite",
        help="Try to automatically fix the offending files (e.g., by re-formatting).",
        action="store_true",
    )
    parser.add_argument(
        "--select",
        help=(
            "If set, only the selected steps are executed. "
            "This is practical if some of the steps failed and you want to "
            "fix them in isolation. "
            "The steps are given as a space-separated list of: "
            + " ".join(value.value for value in Step)
        ),
        metavar="",
        nargs="+",
        choices=[value.value for value in Step],
    )
    parser.add_argument(
        "--skip",
        help=(
            "If set, skips the specified steps. "
            "This is practical if some of the steps passed and "
            "you want to fix the remainder in isolation. "
            "The steps are given as a space-separated list of: "
            + " ".join(value.value for value in Step)
        ),
        metavar="",
        nargs="+",
        choices=[value.value for value in Step],
    )

    args = parser.parse_args()

    overwrite = bool(args.overwrite)

    selects = (
        [Step(value) for value in args.select]
        if args.select is not None
        else [value for value in Step]
    )
    skips = [Step(value) for value in args.skip] if args.skip is not None else []

    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent

    if Step.REFORMAT in selects and Step.REFORMAT not in skips:
        print("Re-formatting...")
        reformat_targets = [
            "aas_core_codegen",
            "continuous_integration",
            "dev_scripts",
            "tests",
            "setup.py",
        ]

        if overwrite:
            exit_code = call_and_report(
                verb="black", cmd=["black"] + reformat_targets, cwd=repo_root
            )
            if exit_code != 0:
                return 1
        else:
            exit_code = call_and_report(
                verb="check with black",
                cmd=["black", "--check"] + reformat_targets,
                cwd=repo_root,
            )
            if exit_code != 0:
                return 1
    else:
        print("Skipped re-formatting.")

    if Step.MYPY in selects and Step.MYPY not in skips:
        print("Mypy'ing...")
        mypy_targets = [
            "aas_core_codegen",
            "tests",
            "continuous_integration",
            "dev_scripts",
        ]
        config_file = pathlib.Path("continuous_integration") / "mypy.ini"

        exit_code = call_and_report(
            verb="mypy",
            cmd=["mypy", "--strict", "--config-file", str(config_file)] + mypy_targets,
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped mypy'ing.")

    if Step.PYLINT in selects and Step.PYLINT not in skips:
        print("Pylint'ing...")
        pylint_targets = [
            "aas_core_codegen",
            "tests",
            "continuous_integration",
            "dev_scripts",
        ]
        rcfile = pathlib.Path("continuous_integration") / "pylint.rc"

        exit_code = call_and_report(
            verb="pylint", cmd=["pylint", f"--rcfile={rcfile}"] + pylint_targets
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped pylint'ing.")

    if (
        Step.CHECK_TEST_META_MODELS_COINCIDE
        and Step.CHECK_TEST_META_MODELS_COINCIDE not in skips
    ):
        groups = [
            [
                repo_root / "test_data/jsonschema/test_main/v3rc1/input/meta_model.py",
                repo_root / "test_data/rdf_shacl/test_main/v3rc1/input/meta_model.py",
            ],
            [
                repo_root / "test_data/csharp/test_main/v3rc2/input/meta_model.py",
                (
                    repo_root / "test_data/intermediate/"
                    "expected/real_meta_models/v3rc2/meta_model.py"
                ),
                repo_root / "test_data/jsonschema/test_main/v3rc2/input/meta_model.py",
                (
                    repo_root / "test_data/parse/"
                    "expected/real_meta_models/v3rc2/meta_model.py"
                ),
            ],
        ]

        for group in groups:
            assert len(group) >= 1, "At least one path expected in a group."
            expected = group[0].read_text(encoding="utf-8").splitlines()
            for pth in group[1:]:
                got = pth.read_text(encoding="utf-8").splitlines()
                if expected != got:
                    print(
                        f"The files {group[0]} and {pth} do not match:", file=sys.stderr
                    )
                    diff = difflib.context_diff(
                        expected, got, fromfile=str(group[0]), tofile=str(pth)
                    )

                    for line in diff:
                        print(line, file=sys.stderr)
                    return 1

    if Step.TEST in selects and Step.TEST not in skips:
        print("Testing...")
        env = os.environ.copy()
        env["ICONTRACT_SLOW"] = "true"

        exit_code = call_and_report(
            verb="execute unit tests",
            cmd=[
                "coverage",
                "run",
                "--source",
                "aas_core_codegen",
                "-m",
                "unittest",
                "discover",
            ],
            cwd=repo_root,
            env=env,
        )
        if exit_code != 0:
            return 1

        exit_code = call_and_report(
            verb="report the coverage", cmd=["coverage", "report"]
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped testing.")

    if Step.DOCTEST in selects and Step.DOCTEST not in skips:
        print("Doctest'ing...")

        # BEFORE-RELEASE (mristin, 2021-12-13):
        #  Add ``{repo_root}/docs/source/**/*.rst`` as well here
        doc_files = ["README.rst"]

        exit_code = call_and_report(
            verb="doctest",
            cmd=[sys.executable, "-m", "doctest"] + doc_files,
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1

        for pth in (repo_root / "aas_core_codegen").glob("**/*.py"):
            if pth.name == "__main__.py":
                continue

            # NOTE (mristin, 2021-12-27):
            # The subprocess calls are expensive, call only if there is an actual
            # doctest
            text = pth.read_text(encoding="utf-8")
            if ">>>" in text:
                exit_code = call_and_report(
                    verb="doctest",
                    cmd=[sys.executable, "-m", "doctest", str(pth)],
                    cwd=repo_root,
                )
                if exit_code != 0:
                    return 1
    else:
        print("Skipped doctest'ing.")

    if (
        Step.CHECK_INIT_AND_SETUP_COINCIDE in selects
        and Step.CHECK_INIT_AND_SETUP_COINCIDE not in skips
    ):
        print("Checking that aas_core_codegen/__init__.py and setup.py coincide...")
        exit_code = call_and_report(
            verb="check that aas_core_codegen/__init__.py and setup.py coincide",
            cmd=[
                sys.executable,
                "continuous_integration/check_init_and_setup_coincide.py",
            ],
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1
    else:
        print(
            "Skipped checking that aas_core_codegen/__init__.py and "
            "setup.py coincide."
        )

    # NOTE (mristin, 2022-01-22):
    # We need to check for the Python version since ``argparse`` output changes
    # between the versions. Hence we pin it at the moment to Python 3.8.

    if sys.version_info < (3, 9):
        if (
            Step.CHECK_HELP_IN_README in selects
            and Step.CHECK_HELP_IN_README not in skips
        ):
            cmd = [sys.executable, "continuous_integration/check_help_in_readme.py"]
            if overwrite:
                cmd.append("--overwrite")

            if not overwrite:
                print("Checking that --help's and the readme coincide...")
                exit_code = call_and_report(
                    verb="check that --help's and the readme coincide",
                    cmd=[
                        sys.executable,
                        "continuous_integration/check_help_in_readme.py",
                    ],
                    cwd=repo_root,
                )
                if exit_code != 0:
                    return 1
            else:
                print("Overwriting the --help's in the readme...")
                exit_code = call_and_report(
                    verb="overwrite the --help's in the readme",
                    cmd=[
                        sys.executable,
                        "continuous_integration/check_help_in_readme.py",
                        "--overwrite",
                    ],
                    cwd=repo_root,
                )
                if exit_code != 0:
                    return 1

            subprocess.check_call(cmd, cwd=str(repo_root))
        else:
            print("Skipped checking that --help's and the doc coincide.")
    else:
        print(
            "Skipped checking that --help's and the doc coincide "
            "since we pin it on Python version 3.8."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
