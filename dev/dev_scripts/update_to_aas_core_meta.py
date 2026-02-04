"""
Update everything in this project to the latest aas-core-meta.

Git is expected to be installed.
"""

import argparse
import os
import pathlib
import subprocess
import sys
import tempfile
import time
from typing import Optional

import dev_scripts.download_latest_aas_core_meta_v3


def _make_sure_no_changed_files(
    repo_dir: pathlib.Path, expected_our_branch: str
) -> Optional[int]:
    """
    Make sure that no files are modified in our repository.

    Return exit code if something is unexpected.
    """
    diff_name_status = subprocess.check_output(
        ["git", "diff", "--name-status", expected_our_branch],
        cwd=str(repo_dir),
        encoding="utf-8",
    ).strip()

    if len(diff_name_status.splitlines()) > 0:
        print(
            f"The following files are modified "
            f"compared to branch {expected_our_branch!r} in {repo_dir}:\n"
            f"{diff_name_status}\n"
            f"\n"
            f"Please stash the changes first before you update to aas-core-meta.",
            file=sys.stderr,
        )
        return 1

    return None


def _rerecord_everything(repo_dir: pathlib.Path) -> Optional[int]:
    """
    Run all unit tests with re-record environment variable set.

    Return an error code, if any.
    """
    env = os.environ.copy()
    env["AAS_CORE_CODEGEN_TESTS_RERECORD"] = "1"

    starting_points = [
        pth
        for pth in (repo_dir / "tests").glob("*")
        if (
            pth.is_dir()
            and not pth.name.startswith("__")
            and not pth.name.startswith(".")
        )
    ]

    start = time.perf_counter()

    for starting_point in starting_points:
        print(f"Starting to run tests in: {starting_point} ...")

        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "--start-directory",
                str(starting_point),
            ],
            env=env,
            cwd=str(repo_dir),
        )

    duration = time.perf_counter() - start
    print(f"Re-recording took: {duration:.2f} seconds.")
    return None


def _create_branch_commit_and_push(
    repo_dir: pathlib.Path, aas_core_meta_revision: str
) -> None:
    """Create a feature branch, commit the changes and push it."""
    branch = f"Update-test-data-to-aas-core-meta-{aas_core_meta_revision}"
    print(f"Creating the branch {branch!r}...")
    subprocess.check_call(["git", "checkout", "-b", branch], cwd=repo_dir)

    print("Adding files...")
    subprocess.check_call(["git", "add", "."], cwd=repo_dir)

    # pylint: disable=line-too-long
    message = f"""\
Update test data to aas-core-meta {aas_core_meta_revision}

We update the development requirements to and re-record the test data
for [aas-core-meta {aas_core_meta_revision}].

[aas-core-meta {aas_core_meta_revision}]: https://github.com/aas-core-works/aas-core-meta/commit/{aas_core_meta_revision}"""
    # pylint: enable=line-too-long

    print("Committing...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = pathlib.Path(tmp_dir) / "commit-message.txt"
        tmp_file.write_text(message, encoding="utf-8")

        subprocess.check_call(["git", "commit", "--file", str(tmp_file)], cwd=repo_dir)

    print(f"Pushing to remote {branch}...")
    subprocess.check_call(["git", "push", "-u"], cwd=repo_dir)


def main() -> int:
    """Execute the main routine."""
    repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected_our_branch",
        help="Git branch expected in this repository",
        default="main",
    )
    args = parser.parse_args()

    expected_our_branch = str(args.expected_our_branch)

    our_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(repo_dir),
        encoding="utf-8",
    ).strip()
    if our_branch != expected_our_branch:
        print(
            f"--expected_our_branch is {expected_our_branch}, "
            f"but got {our_branch} in: {repo_dir}",
            file=sys.stderr,
        )
        return 1

    exit_code = _make_sure_no_changed_files(
        repo_dir=repo_dir, expected_our_branch=expected_our_branch
    )
    if exit_code is not None:
        return exit_code

    # fmt: off
    aas_core_meta_revision = (
        dev_scripts.download_latest_aas_core_meta_v3.retrieve_sha_and_download()
    )[:8]
    # fmt: on

    print(f"The aas-core-meta revision is: {aas_core_meta_revision}")

    exit_code = _rerecord_everything(repo_dir=repo_dir)
    if exit_code is not None:
        return exit_code

    _create_branch_commit_and_push(
        repo_dir=repo_dir, aas_core_meta_revision=aas_core_meta_revision
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
