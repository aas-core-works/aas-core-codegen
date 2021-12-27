"""Encapsulate the entry point to different generators."""
import pathlib
import textwrap
from typing import Sequence, TextIO

from icontract import require

from aas_core_codegen import specific_implementations, intermediate
from aas_core_codegen.common import LinenoColumner


class Context:
    """Represent the context of a code generation."""

    @require(lambda model_path: model_path.exists() and model_path.is_file())
    @require(lambda output_dir: output_dir.exists() and output_dir.is_dir())
    def __init__(
        self,
        model_path: pathlib.Path,
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations,
        lineno_columner: LinenoColumner,
        output_dir: pathlib.Path,
    ) -> None:
        """Initialize with the given values."""
        self.model_path = model_path
        self.symbol_table = symbol_table
        self.spec_impls = spec_impls
        self.lineno_columner = lineno_columner
        self.output_dir = output_dir


@require(
    lambda errors: all(
        len(error) > 0 and not error.startswith("\n")
        # This is necessary so that we do not have double bullet point.
        and not error.startswith("*") and not error.endswith("\n")
        for error in errors
    )
)
@require(lambda message: not message.endswith(":"))
@require(lambda message: not message.endswith("\n"))
@require(lambda message: not message.startswith("\n") and not message.startswith("*"))
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
