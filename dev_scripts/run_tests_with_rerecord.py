"""Run all the tests with the environment variable ``AAS_CORE_CODEGEN_RERECORD`` set."""

import argparse
import os
import pathlib
import subprocess
import sys
import shlex


def main() -> int:
    """Execute the main routine."""
    available_tests = [
        "tests.csharp.test_main.Test_against_recorded",
        "tests.csharp.test_verification.Test_against_recorded",
        "tests.csharp.test_structure.Test_generation_against_recorded",
        "tests.intermediate.test_translate.Test_against_recorded",
        "tests.our_jsonschema.test_main.Test_against_recorded",
        "tests.rdf_shacl.test_main.Test_against_recorded",
        "tests.parse.test_parse.Test_against_recorded",
        "tests.parse.test_retree.Test_against_recorded",
        "tests.smoke.test_main.Test_against_recorded",
        "tests.xsd.test_main.Test_against_recorded",
    ]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--select",
        help=(
            "If set, only the selected tests are executed. "
            "This is practical if some of the tests failed and you want to "
            "fix them in isolation. "
            "The tests are given as a space-separated list of: "
            + " ".join(available_tests)
        ),
        metavar="",
        nargs="+",
        choices=available_tests,
    )
    args = parser.parse_args()

    this_path = pathlib.Path(os.path.realpath(__file__))
    repo_root = this_path.parent.parent

    env = os.environ.copy()
    env["AAS_CORE_CODEGEN_RERECORD"] = "1"

    if args.select is not None:
        tests_to_run = list(args.select)
    else:
        tests_to_run = available_tests

    for qualified_test_name in tests_to_run:
        cmd = [sys.executable, "-m", "unittest", "-v", qualified_test_name]

        print(f"Executing {qualified_test_name}...")
        exit_code = subprocess.call(cmd, cwd=str(repo_root), env=env)
        if exit_code != 0:
            cmd_str = " ".join(shlex.quote(part) for part in cmd)
            print(f"Failed to execute the test: {cmd_str}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
