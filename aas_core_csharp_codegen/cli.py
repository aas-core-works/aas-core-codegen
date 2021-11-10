"""Provide functions for user experience in the command line."""

# fmt: off
import textwrap
from typing import Sequence, TextIO

from icontract import require


@require(
    lambda errors:
    all(
        len(error) > 0
        and not error.startswith('\n')
        # This is necessary so that we do not have double bullet point.
        and not error.startswith('*')
        and not error.endswith('\n')
        for error in errors
    )
)
@require(lambda message: not message.endswith(':'))
@require(lambda message: not message.endswith('\n'))
@require(
    lambda message:
    not message.startswith('\n')
    and not message.startswith('*')
)
# fmt: on
def write_error_report(message: str, errors: Sequence[str], stderr: TextIO) -> None:
    """
    Write the report (main ``message`` and details as ``errors``) to ``stderr``.

    This method helps us to have a unified way of showing errors.
    """
    stderr.write(f"{message}:\n")
    for error in errors:
        indented = textwrap.indent(error, "  ")
        indented = "* " + indented[2:]
        stderr.write(f"{indented}\n")
