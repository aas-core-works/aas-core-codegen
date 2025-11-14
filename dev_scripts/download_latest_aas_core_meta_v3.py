"""Download the latest meta-model for V3.0 to the test data."""

import argparse
import os
import pathlib
import sys
from typing import Final, Mapping, Union

import black
import requests

OWNER: Final[str] = "aas-core-works"
REPO: Final[str] = "aas-core-meta"
REF: Final[str] = "main"
REMOTE_PATH: Final[str] = "aas_core_meta/v3.py"


def _latest_commit_sha(timeout: float = 15.0) -> str:
    """Resolve the latest commit SHA on the ``REF`` for a specific path."""
    params: Mapping[str, Union[str, int]] = {
        "path": REMOTE_PATH,
        "sha": REF,
        "per_page": 1,
    }
    resp = requests.get(
        f"https://api.github.com/repos/{OWNER}/{REPO}/commits",
        params=params,
        timeout=timeout,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as ex:
        raise RuntimeError(
            f"Failed to resolve latest commit for "
            f"{OWNER}/{REPO}:{REF} path={REMOTE_PATH} "
            f"({resp.status_code}): {resp.text}"
        ) from ex

    commits = resp.json()
    if not commits or not isinstance(commits, list):
        raise RuntimeError(
            "Could not determine latest commit SHA (empty API response)."
        )

    sha = commits[0].get("sha")
    if not isinstance(sha, str):
        raise RuntimeError("API did not return a valid commit SHA.")

    if len(sha) == 0:
        raise RuntimeError("API returned an empty commit SHA.")

    return sha


def _raw_url(sha: str) -> str:
    """Get the URL of the raw file on GitHub."""
    return f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{sha}/{REMOTE_PATH}"


def _download(url: str, timeout: float = 30.0) -> str:
    """Download the raw file contents."""
    resp = requests.get(url, timeout=timeout)
    try:
        resp.raise_for_status()
    except requests.HTTPError as ex:
        raise RuntimeError(
            f"Failed to download file from {url} ({resp.status_code}): {resp.text}"
        ) from ex

    return resp.text


def retrieve_sha_and_download() -> str:
    """
    Get the latest SHA revision of the meta-model and download it to test data.

    Return the SHA of the downloaded meta-model.
    """
    sha = _latest_commit_sha()

    raw_url = _raw_url(sha)

    content = _download(url=raw_url)

    banner = f"# Downloaded from: {raw_url}\n# Do NOT edit or append!"

    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent

    out_path = repo_root / "test_data/real_meta_models/aas_core_meta.v3.py"
    out_path.parent.mkdir(exist_ok=True)

    out_path.write_text(f"{banner}\n\n{content.rstrip()}\n\n{banner}", encoding="utf-8")

    black.format_file_in_place(
        src=out_path, fast=False, mode=black.FileMode(), write_back=black.WriteBack.YES
    )

    print(f"Wrote and reformatted to: {out_path} (from commit {sha[:8]}).")

    return sha


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    retrieve_sha_and_download()

    return 0


if __name__ == "__main__":
    sys.exit(main())
