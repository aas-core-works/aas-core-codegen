"""Run integration tests on the Java generated code."""

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

    if shutil.which("mvn") is None:
        print(
            "mvn (Maven) could not be found on your PATH -- "
            "have you installed Maven?",
            file=sys.stderr,
        )
        return 1

    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

    main_java_expected_dir = (
        repo_root / "dev" / "test_data" / "main" / "java" / "expected"
    )

    assert main_java_expected_dir.exists() and main_java_expected_dir.is_dir()

    live_tests_java_dir = repo_root / "dev" / "test_data" / "live_tests" / "java"

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
            path for path in main_java_expected_dir.iterdir() if path.is_dir()
        ):
            if select is not None and select.match(case_dir.name) is None:
                print(f"Skipping {case_dir.name} since not selected.")
                continue

            print(f"Running the live test on {case_dir.name} ...")

            project_dir = output_dir / case_dir.name
            project_dir.mkdir(exist_ok=True)

            package = Stripped(
                (case_dir / "input" / "snippets" / "package.txt")
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
                # We check whether there is a change to avoid unnecessary
                # recompilations due to modification timestamps of the files.

                if not target_path.exists() or target_path.read_text(
                    encoding="utf-8"
                ) != path.read_text(encoding="utf-8"):
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(path, target_path)

            group_id = package
            artifact_id = "-".join(package.split("."))

            (project_dir / "pom.xml").write_text(
                f"""\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 \
http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <groupId>{group_id}</groupId>
  <artifactId>{artifact_id}</artifactId>
  <version>0.0.1</version>
  <packaging>jar</packaging>

  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>

  <dependencies>
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>2.17.2</version>
    </dependency>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>5.10.3</version>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.13.0</version>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.5</version>
      </plugin>
    </plugins>
  </build>
</project>
""",
                encoding="utf-8",
            )

            cmd = ["mvn", "--batch-mode", "test-compile"]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {project_dir}"
            )
            subprocess.check_call(cmd, cwd=project_dir)

            case_test_data_dir = live_tests_java_dir / "test_data" / case_dir.name

            if not case_test_data_dir.exists():
                # NOTE (mristin):
                # We fall back to the shared test data.
                case_test_data_dir = live_tests_common.common_test_data_dir_for_case(
                    case_name=case_dir.name
                )

            if case_test_data_dir.exists():
                # NOTE (mristin):
                # Java expects the test data in ``test_data`` relative to the working
                # directory of the JVM process, which, by default, is the base
                # directory of the Maven module (see ``Common.TEST_DATA_DIR`` in the
                # generated test code).
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

                env_var_prefix = re.sub(
                    r"(?<=[a-z])(?=[A-Z])", "_", package.replace(".", "_")
                ).upper()

                cmd = ["mvn", "--batch-mode", "test"]
                env = os.environ.copy()

                env_var_test_record_mode = f"{env_var_prefix}_TESTS_RECORD_MODE"
                env[env_var_test_record_mode] = "1"

                print(
                    f"Running "
                    f"{env_var_test_record_mode}"
                    f"={env.get(env_var_test_record_mode)} "
                    f"{live_tests_common.escape_and_join_command(cmd)} "
                    f"in {project_dir}"
                )
                subprocess.check_call(cmd, cwd=project_dir, env=env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
