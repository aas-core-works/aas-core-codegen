#!/usr/bin/env python3
"""Run pre-commit checks on the repository."""
import argparse
import enum
import os
import pathlib
import subprocess
import sys


class Step(enum.Enum):
    BLACK = "black"
    MYPY = "mypy"
    PYLINT = "pylint"
    TEST = "test"
    DOCTEST = "doctest"
    CHECK_INIT_AND_SETUP_COINCIDE = "check-init-and-setup-coincide"
    CHECK_HELP_IN_README = "check-help-in-readme"


def main() -> int:
    """"Execute entry_point routine."""
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

    repo_root = pathlib.Path(__file__).parent

    if Step.BLACK in selects and Step.BLACK not in skips:
        print("Black'ing...")
        # fmt: off
        black_targets = [
            "aas_core_codegen",
            "precommit.py",
            "setup.py",
            "check_init_and_setup_coincide.py",
            "check_help_in_readme.py"
        ]
        # fmt: on

        if overwrite:
            subprocess.check_call(["black"] + black_targets, cwd=str(repo_root))
        else:
            subprocess.check_call(
                ["black", "--check"] + black_targets, cwd=str(repo_root)
            )
    else:
        print("Skipped black'ing.")

    if Step.MYPY in selects and Step.MYPY not in skips:
        print("Mypy'ing...")
        # fmt: off
        mypy_targets = ["aas_core_codegen", "tests"]
        subprocess.check_call(["mypy", "--strict"] + mypy_targets, cwd=str(repo_root))
        # fmt: on
    else:
        print("Skipped mypy'ing.")

    if Step.PYLINT in selects and Step.PYLINT not in skips:
        # fmt: off
        print("Pylint'ing...")
        pylint_targets = ["aas_core_codegen"]
        subprocess.check_call(
            ["pylint", "--rcfile=pylint.rc"] + pylint_targets, cwd=str(repo_root)
        )
        # fmt: on
    else:
        print("Skipped pylint'ing.")

    if Step.TEST in selects and Step.TEST not in skips:
        print("Testing...")
        env = os.environ.copy()
        env["ICONTRACT_SLOW"] = "true"

        # fmt: off
        subprocess.check_call(
            [
                "coverage", "run",
                "--source", "aas_core_codegen",
                "-m", "unittest", "discover"
            ],
            cwd=str(repo_root),
            env=env
        )
        # fmt: on

        subprocess.check_call(["coverage", "report"])
    else:
        print("Skipped testing.")

    if Step.DOCTEST in selects and Step.DOCTEST not in skips:
        # We doctest the documentation in a separate step from testing so that
        # the two steps can run in isolation.
        #
        # It is indeed possible to doctest the documentation *together* with
        # the other tests (and even measure the code coverage),
        # but this is not desirable as tests can take quite long to run.
        # This would slow down the development if all we want is to iterate
        # on documentation doctests.
        print("Doctesting...")
        subprocess.check_call([sys.executable, "-m", "doctest", "README.rst"])
    else:
        print("Skipped doctesting.")

    if (
        Step.CHECK_INIT_AND_SETUP_COINCIDE in selects
        and Step.CHECK_INIT_AND_SETUP_COINCIDE not in skips
    ):
        print(
            "Checking that aas_core_codegen/__init__.py and setup.py coincide..."
        )
        subprocess.check_call([sys.executable, "check_init_and_setup_coincide.py"])
    else:
        print(
            "Skipped checking that aas_core_codegen/__init__.py and "
            "setup.py coincide."
        )

    if Step.CHECK_HELP_IN_README in selects and Step.CHECK_HELP_IN_README not in skips:
        cmd = [sys.executable, "check_help_in_readme.py"]
        if overwrite:
            cmd.append("--overwrite")

        if not overwrite:
            print("Checking that --help's and the doc coincide...")
        else:
            print("Overwriting the --help's in the doc...")

        subprocess.check_call(cmd)
    else:
        print("Skipped checking that --help's and the doc coincide.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
