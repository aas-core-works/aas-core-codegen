"""
Transpile the meta-model into C# and compile them into a project.

This live tests expects dotnet to be installed on the machine.
"""
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap

import aas_core_meta.v3rc2

import aas_core_codegen.main


def main() -> int:
    """Execute the main routine."""
    print("Running dotnet --version to check that dotnet is available...")
    exit_code = subprocess.call(
        ["dotnet", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if exit_code != 0:
        print(
            f"Failed to execute ``dotnet --version`` "
            f"with the exit code {exit_code}. Is dotnet installed?",
            file=sys.stderr,
        )
        return 1

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        parent_case_dir = repo_dir / "test_data" / "csharp" / "test_main"
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        for module in [aas_core_meta.v3rc2]:
            case_dir = parent_case_dir / module.__name__
            assert case_dir.is_dir(), case_dir

            assert (
                module.__file__ is not None
            ), f"Expected the module {module!r} to have a __file__, but it has None"
            model_pth = pathlib.Path(module.__file__)
            assert model_pth.exists() and model_pth.is_file(), model_pth

            snippets_dir = case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            output_dir = pathlib.Path(tmp_dir) / case_dir.name

            print(
                f"Generating the files based on the case {case_dir} "
                f"to: {output_dir} ..."
            )

            output_dir.mkdir(exist_ok=True, parents=True)

            params = aas_core_codegen.main.Parameters(
                model_path=model_pth,
                target=aas_core_codegen.main.Target.CSHARP,
                snippets_dir=snippets_dir,
                output_dir=output_dir,
            )

            stdout = io.StringIO()
            stderr = io.StringIO()

            return_code = aas_core_codegen.main.execute(
                params=params, stdout=stdout, stderr=stderr
            )

            assert (
                stderr.getvalue() == ""
            ), f"Expected no stderr on valid models, but got:\n{stderr.getvalue()}"

            assert (
                return_code == 0
            ), f"Expected return code 0 on valid models, but got: {return_code}"

            print("Generating the .csproj file...")
            csproj_pth = output_dir / "SomeProject.csproj"
            csproj_pth.write_text(
                textwrap.dedent(
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
                """
                ),
                encoding="utf-8",
            )

            print("Calling dotnet build...")
            exit_code = subprocess.call(["dotnet", "build", "."], cwd=str(output_dir))
            if exit_code != 0:
                print(
                    f"ERROR: Expected the build to succeed, "
                    f"but got exit code: {exit_code}",
                    file=sys.stderr,
                )
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
