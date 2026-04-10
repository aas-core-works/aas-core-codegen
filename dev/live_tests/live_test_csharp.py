"""Run integration tests on the C# generated code."""

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

    main_csharp_expected_dir = (
        repo_root / "dev" / "test_data" / "main" / "csharp" / "expected"
    )

    assert main_csharp_expected_dir.exists() and main_csharp_expected_dir.is_dir()

    live_tests_csharp_dir = repo_root / "dev" / "test_data" / "live_tests" / "csharp"
    assert (
        live_tests_csharp_dir.exists() and live_tests_csharp_dir.is_dir()
    ), live_tests_csharp_dir

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
            path for path in main_csharp_expected_dir.iterdir() if path.is_dir()
        ):
            if select is not None and select.match(case_dir.name) is None:
                print(f"Skipping {case_dir.name} since not selected.")
                continue

            print(f"Running the live test on {case_dir.name} ...")

            solution_dir = output_dir / case_dir.name
            solution_dir.mkdir(exist_ok=True)

            namespace = Stripped(
                (case_dir / "input" / "snippets" / "namespace.txt")
                .read_text(encoding="utf-8")
                .strip()
            )

            expected_output_dir = case_dir / "expected_output"

            print(
                f"Copying all the files from {expected_output_dir} to {solution_dir} ..."
            )
            for path in sorted(
                path
                for path in expected_output_dir.glob("**/*")
                if path.name != "stdout.txt" and path.is_file()
            ):
                target_path = solution_dir / (path.relative_to(expected_output_dir))

                # NOTE (mristin):
                # We check whether there is a change to avoid unnecessary recompilations
                # due to modification timestamps of the files.

                if not target_path.exists() or target_path.read_text(
                    encoding="utf-8"
                ) != path.read_text(encoding="utf-8"):
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(path, target_path)

            (solution_dir / namespace / f"{namespace}.csproj").write_text(
                """\
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <Nullable>enable</Nullable>
    <Configurations>Debug;Release;DebugSlow</Configurations>
    <Platforms>AnyCPU</Platforms>
    <LangVersion>8</LangVersion>
  </PropertyGroup>
</Project>
""",
                encoding="utf-8",
            )

            (
                solution_dir / f"{namespace}.Tests" / f"{namespace}.Tests.csproj"
            ).write_text(
                f"""\
<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
        <TargetFramework>net6.0</TargetFramework>
        <IsPackable>false</IsPackable>
        <Configurations>Debug;Release;DebugSlow</Configurations>
        <Platforms>AnyCPU</Platforms>
        <Nullable>enable</Nullable>
        <OutputType>Library</OutputType>
        <LangVersion>8</LangVersion>
    </PropertyGroup>

    <PropertyGroup Condition=" '$(Configuration)' == 'Debug' ">
      <DefineConstants>TRACECOREAPP</DefineConstants>
    </PropertyGroup>

    <ItemGroup>
        <PackageReference Include="NUnit" Version="3.13.3" />
        <PackageReference Include="NUnit3TestAdapter" Version="4.2.1" />
        <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.1.0" />
        <PackageReference Include="OpenCover" Version="4.7.1221" />
        <PackageReference Include="coverlet.msbuild" Version="3.1.2">
          <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
          <PrivateAssets>all</PrivateAssets>
        </PackageReference>
    </ItemGroup>

    <ItemGroup>
      <ProjectReference Include="../{namespace}/{namespace}.csproj" />
    </ItemGroup>

    <ItemGroup>
      <None Update="TestResources/**">
        <CopyToOutputDirectory>Always</CopyToOutputDirectory>
      </None>
    </ItemGroup>
</Project>
""",
                encoding="utf-8",
            )

            solution_name = "-".join(part.lower() for part in namespace.split("."))

            cmd = ["dotnet", "new", "sln", "-n", solution_name, "--force"]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {solution_dir} ..."
            )
            subprocess.check_call(cmd, cwd=solution_dir)

            cmd = [
                "dotnet",
                "sln",
                f"{solution_name}.sln",
                "add",
                f"{namespace}/{namespace}.csproj",
                f"{namespace}.Tests/{namespace}.Tests.csproj",
            ]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {solution_dir} ..."
            )
            subprocess.check_call(cmd, cwd=solution_dir)

            cmd = ["dotnet", "build"]
            print(
                f"Running {live_tests_common.escape_and_join_command(cmd)} "
                f"in {solution_dir} ..."
            )
            subprocess.check_call(cmd, cwd=solution_dir)

            case_test_data_dir = live_tests_csharp_dir / "test_data" / case_dir.name
            if case_test_data_dir.exists():
                target_test_data = solution_dir / "test_data"
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

                env_var_prefix = "_".join(part.upper() for part in namespace.split("."))

                cmd = ["dotnet", "test"]
                env = os.environ.copy()

                env_var_test_data_dir = f"{env_var_prefix}_TESTS_TEST_DATA_DIR"
                env_var_test_record_mode = f"{env_var_prefix}_TESTS_RECORD_MODE"

                env[env_var_test_data_dir] = str(solution_dir / "test_data")
                env[env_var_test_record_mode] = "1"

                print(
                    f"Running "
                    f"{env_var_test_data_dir}"
                    f"={env.get(env_var_test_data_dir)} "
                    f"{env_var_test_record_mode}"
                    f"={env.get(env_var_test_record_mode)} "
                    f"{live_tests_common.escape_and_join_command(cmd)} "
                    f"in {solution_dir}"
                )
                subprocess.check_call(cmd, cwd=solution_dir, env=env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
