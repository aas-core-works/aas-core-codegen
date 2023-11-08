"""Generate Java code to handle asset administration shells based on the meta-model."""
from typing import TextIO

from aas_core_codegen import run

def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""

    _ = context
    _ = stderr

    stdout.write("java generator called, nothing too fancy\n")

    return 1
