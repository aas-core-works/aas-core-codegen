#!/usr/bin/env python3
"""Run pre-commit checks on the repository."""
import argparse
import enum
import os
import pathlib
import subprocess
import sys


class Step(enum.Enum):
    REFORMAT = "reformat"
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

    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent

    if Step.REFORMAT in selects and Step.REFORMAT not in skips:
        print("Re-formatting...")
        # fmt: off
        reformat_targets = [
            "aas_core_codegen",
            "continuous_integration",
            "tests",
            "setup.py"
        ]
        # fmt: on

        if overwrite:
            subprocess.check_call(["black"] + reformat_targets, cwd=str(repo_root))
        else:
            subprocess.check_call(
                ["black", "--check"] + reformat_targets, cwd=str(repo_root)
            )
    else:
        print("Skipped re-formatting.")

    if Step.MYPY in selects and Step.MYPY not in skips:
        print("Mypy'ing...")
        # fmt: off
        mypy_targets = [
            "aas_core_codegen",
            "tests",
            "continuous_integration"
        ]

        config_file = pathlib.Path("continuous_integration") / "mypy.ini"

        subprocess.check_call(
            ["mypy", "--strict", f"--config-file", str(config_file)] + mypy_targets,
            cwd=str(repo_root))
        # fmt: on
    else:
        print("Skipped mypy'ing.")

    if Step.PYLINT in selects and Step.PYLINT not in skips:
        # fmt: off
        print("Pylint'ing...")
        pylint_targets = ["aas_core_codegen"]
        rcfile = pathlib.Path("continuous_integration") / "pylint.rc"

        subprocess.check_call(
            ["pylint", f"--rcfile={rcfile}"] + pylint_targets, cwd=str(repo_root)
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

        subprocess.check_call(
            ["coverage", "report"],
            cwd=str(repo_root),
        )
    else:
        print("Skipped testing.")

    if Step.DOCTEST in selects and Step.DOCTEST not in skips:
        print("Doctest'ing...")

        doc_files = ["README.rst"]
        # BEFORE-RELEASE (mristin, 2021-12-13):
        #  Add ``{repo_root}/docs/source/**/*.rst`` as well here
        subprocess.check_call(
            [sys.executable, "-m", "doctest"] + doc_files, cwd=str(repo_root)
        )

        for pth in (repo_root / "aas_core_codegen").glob("**/*.py"):
            subprocess.check_call(
                [sys.executable, "-m", "doctest", str(pth)], cwd=str(repo_root)
            )

    else:
        print("Skipped doctest'ing.")

    if (
        Step.CHECK_INIT_AND_SETUP_COINCIDE in selects
        and Step.CHECK_INIT_AND_SETUP_COINCIDE not in skips
    ):
        print("Checking that aas_core_codegen/__init__.py and setup.py coincide...")
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
            print("Checking that --help's and the readme coincide...")
        else:
            print("Overwriting the --help's in the readme...")

        subprocess.check_call(cmd)
    else:
        print("Skipped checking that --help's and the doc coincide.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
