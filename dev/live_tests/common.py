"""Provide common functionality shared across the live tests."""
import os
import pathlib
import shlex
from typing import Sequence, Final


def escape_and_join_command(command: Sequence[str]) -> str:
    """Prepare the command and join it so that you can copy+paste+run it in console."""
    return " ".join(shlex.quote(part) for part in command)


_REPO_ROOT: Final[pathlib.Path] = pathlib.Path(
    os.path.realpath(__file__)
).parent.parent.parent


def common_test_data_dir_for_case(case_name: str) -> pathlib.Path:
    """Determine the path to the shared test data directory for the given case."""
    return (
        _REPO_ROOT / "dev" / "test_data" / "live_tests" / "common_test_data" / case_name
    )
