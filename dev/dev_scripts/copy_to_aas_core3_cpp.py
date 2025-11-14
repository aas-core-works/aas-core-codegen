"""
Copy the generated C++ files for AAS v3.0 to the corresponding C++ repository.

This script is practical as a part of the development pipeline:
1) Re-generate C++ files (through re-recording the test data),
2) Copy the generated files (with this script),
3) Run clang-format and clang-tidy from the C++ repository, and
4) Run the unit tests from the C++ repository.
"""

import argparse
import os
import pathlib
import shutil
import sys


def main() -> int:
    """Execute the main routine."""
    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aas_core3_cpp_path",
        help="Path to the aas-core3.0-cpp repository",
        default=str(repo_root.parent / "aas-core3.0-cpp"),
    )
    args = parser.parse_args()

    aas_core3_cpp_path = pathlib.Path(args.aas_core3_cpp_path)

    if not aas_core3_cpp_path.exists():
        print(
            f"--aas_core3_cpp_path does not exist: {aas_core3_cpp_path}",
            file=sys.stderr,
        )
        return 1

    if not aas_core3_cpp_path.is_dir():
        print(
            f"--aas_core3_cpp_path is not a directory: {aas_core3_cpp_path}",
            file=sys.stderr,
        )
        return 1

    expected_output_dir = (
        repo_root
        / "dev"
        / "test_data"
        / "cpp"
        / "test_main"
        / "aas_core_meta.v3"
        / "expected_output"
    )

    assert aas_core3_cpp_path.exists()

    target_src_dir = aas_core3_cpp_path / "src"
    target_src_dir.mkdir(exist_ok=True)

    target_include_dir = aas_core3_cpp_path / "include" / "aas_core" / "aas_3_0"
    target_include_dir.mkdir(exist_ok=True, parents=True)

    paths = sorted(
        list(expected_output_dir.glob("*.cpp"))
        + list(expected_output_dir.glob("*.hpp"))
    )

    print(
        f"Copying *.cpp and *.hpp\n"
        f"  from {expected_output_dir}\n"
        f"  to {target_src_dir} and {target_include_dir}..."
    )
    for pth in paths:
        if pth.suffix == ".cpp":
            dst = target_src_dir / pth.name
        elif pth.suffix == ".hpp":
            dst = target_include_dir / pth.name
        else:
            raise AssertionError(f"Unhandled suffix: {pth.suffix} from: {pth}")

        # NOTE (mristin, 2024-01-08):
        # We compare the contents to avoid re-compilations by CMake.
        should_copy = True
        if dst.exists():
            src_text = pth.read_text(encoding="utf-8")
            dst_text = dst.read_text(encoding="utf-8")

            should_copy = src_text != dst_text

        if should_copy:
            shutil.copy(src=pth, dst=dst)

    print("Copied.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
