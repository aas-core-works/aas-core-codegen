"""
Update everything in this project to the latest aas-core-meta.

Git is expected to be installed.
"""

import argparse
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
from typing import Optional, List, MutableMapping

AAS_CORE_META_DEPENDENCY_RE = re.compile(
    r"aas-core-meta@git\+https://github.com/aas-core-works/aas-core-meta@([a-fA-F0-9]+)#egg=aas-core-meta"
)


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


def _update_setup_py(repo_dir: pathlib.Path, aas_core_meta_revision: str) -> None:
    """Update the aas-core-meta in setup.py."""
    setup_py = repo_dir / "setup.py"
    text = setup_py.read_text(encoding="utf-8")

    aas_core_meta_dependency = (
        f"aas-core-meta@git+https://github.com/aas-core-works/aas-core-meta"
        f"@{aas_core_meta_revision}#egg=aas-core-meta"
    )

    text = re.sub(AAS_CORE_META_DEPENDENCY_RE, aas_core_meta_dependency, text)

    setup_py.write_text(text, encoding="utf-8")


def _uninstall_and_install_aas_core_meta(
    repo_dir: pathlib.Path, aas_core_meta_revision: str
) -> None:
    """Uninstall and install the latest aas-core-meta in the virtual environment."""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "uninstall", "-y", "aas-core-meta"],
        cwd=str(repo_dir),
    )

    aas_core_meta_dependency = (
        f"aas-core-meta@git+https://github.com/aas-core-works/aas-core-meta"
        f"@{aas_core_meta_revision}#egg=aas-core-meta"
    )

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", aas_core_meta_dependency],
        cwd=str(repo_dir),
    )


def _rerecord_everything(repo_dir: pathlib.Path) -> Optional[int]:
    """
    Run all unit tests with re-record environment variable set.

    Return an error code, if any.
    """
    env = os.environ.copy()
    env["AAS_CORE_CODEGEN_RERECORD"] = "1"

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
            cwd=str(repo_dir)
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
    this_path = pathlib.Path(os.path.realpath(__file__))
    repo_dir = this_path.parent.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aas_core_meta_repo",
        help="path to the aas-core-meta repository",
        default=str(repo_dir.parent / "aas-core-meta"),
    )
    parser.add_argument(
        "--expected_our_branch",
        help="Git branch expected in this repository",
        default="main",
    )
    parser.add_argument(
        "--expected_aas_core_meta_branch",
        help="Git branch expected in the aas-core-meta repository",
        default="main",
    )
    args = parser.parse_args()

    aas_core_meta_repo = pathlib.Path(args.aas_core_meta_repo)
    expected_our_branch = str(args.expected_our_branch)
    expected_aas_core_meta_branch = str(args.expected_aas_core_meta_branch)

    if not aas_core_meta_repo.exists():
        print(
            f"--aas_core_meta_repo does not exist: {aas_core_meta_repo}",
            file=sys.stderr,
        )
        return 1

    if not aas_core_meta_repo.is_dir():
        print(
            f"--aas_core_meta_repo is not a directory: {aas_core_meta_repo}",
            file=sys.stderr,
        )
        return 1

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

    aas_core_meta_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(aas_core_meta_repo),
        encoding="utf-8",
    ).strip()
    if aas_core_meta_branch != expected_aas_core_meta_branch:
        print(
            f"--expected_aas_core_meta_branch is {expected_aas_core_meta_branch}, "
            f"but got {aas_core_meta_branch} "
            f"in --aas_core_meta_repo: {aas_core_meta_repo}",
            file=sys.stderr,
        )
        return 1

    aas_core_meta_revision = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(aas_core_meta_repo),
        encoding="utf-8",
    ).strip()

    exit_code = _make_sure_no_changed_files(
        repo_dir=repo_dir, expected_our_branch=expected_our_branch
    )
    if exit_code is not None:
        return exit_code

    _update_setup_py(repo_dir=repo_dir, aas_core_meta_revision=aas_core_meta_revision)

    _uninstall_and_install_aas_core_meta(
        repo_dir=repo_dir, aas_core_meta_revision=aas_core_meta_revision
    )

    exit_code = _rerecord_everything(repo_dir=repo_dir)
    if exit_code is not None:
        return exit_code

    _create_branch_commit_and_push(
        repo_dir=repo_dir, aas_core_meta_revision=aas_core_meta_revision
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
