"""Run all the tests with the environment variable ``AAS_CORE_CODEGEN_RERECORD`` set."""

import argparse
import os
import pathlib
import subprocess
import sys
import shlex


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    this_path = pathlib.Path(os.path.realpath(__file__))
    repo_root = this_path.parent.parent

    env = os.environ.copy()
    env["AAS_CORE_CODEGEN_RERECORD"] = "1"

    tests_to_run = [
        "tests.csharp.test_main.Test_against_recorded",
        "tests.intermediate.test_translate.Test_against_recorded",
        "tests.jsonschema.test_main.Test_against_recorded",
        "tests.rdf_shacl.test_main.Test_against_recorded",
        "tests.test_parse.Test_against_recorded",
    ]

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
