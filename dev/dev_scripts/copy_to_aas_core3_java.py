"""
Copy the generated Java files for AAS v3.0 to the corresponding Java repository.

This script is practical as a part of the development pipeline:
1) Re-generate Java files (through re-recording the test data),
2) Copy the generated files (with this script),
3) Run the checks and reformatting from the Java repository, and
4) Re-generate the javadoc.
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
        "--aas_core3_java_path",
        help="Path to the aas-core3.0-java repository",
        default=str(repo_root.parent / "aas-core3.0-java"),
    )
    args = parser.parse_args()

    aas_core3_java_path = pathlib.Path(args.aas_core3_java_path)

    if not aas_core3_java_path.exists():
        print(
            f"--aas_core3_java_path does not exist: {aas_core3_java_path}",
            file=sys.stderr,
        )
        return 1

    if not aas_core3_java_path.is_dir():
        print(
            f"--aas_core3_java_path is not a directory: {aas_core3_java_path}",
            file=sys.stderr,
        )
        return 1

    expected_output_dir = (
        repo_root
        / "dev"
        / "test_data"
        / "java"
        / "test_main"
        / "aas_core_meta.v3"
        / "expected_output"
    )

    assert aas_core3_java_path.exists()

    target_src_dir = aas_core3_java_path / "src/main/java/aas_core/aas3_0"
    target_src_dir.mkdir(exist_ok=True)

    paths = sorted(expected_output_dir.glob("**/*.java"))

    print(
        f"Copying *.java\n"
        f"  from {expected_output_dir}\n"
        f"  to {target_src_dir}..."
    )
    for pth in paths:
        dst = target_src_dir / pth.relative_to(expected_output_dir)

        # NOTE (mristin):
        # We compare the contents to avoid re-compilations.
        should_copy = True
        if dst.exists():
            src_text = pth.read_text(encoding="utf-8")
            dst_text = dst.read_text(encoding="utf-8")

            should_copy = src_text != dst_text

        if should_copy:
            print(f"    Copying {pth} to {dst}...")
            shutil.copy(src=pth, dst=dst)

    print("Copied.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
