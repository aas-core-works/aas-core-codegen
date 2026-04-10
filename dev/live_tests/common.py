"""Provide common functionality shared across the live tests."""
import shlex
from typing import Sequence


def escape_and_join_command(command: Sequence[str]) -> str:
    """Prepare the command and join it so that you can copy+paste+run it in console."""
    return " ".join(shlex.quote(part) for part in command)
