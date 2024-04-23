"""Encapsulate the entry point to different generators."""
import io
import pathlib
import textwrap
from typing import Sequence, TextIO, Tuple, Optional

import asttokens
from icontract import require, ensure

from aas_core_codegen import specific_implementations, intermediate, parse
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


@require(lambda model_path: model_path.exists() and model_path.is_file())
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def load_model(
    model_path: pathlib.Path,
) -> Tuple[
    Optional[Tuple[intermediate.SymbolTable, asttokens.ASTTokens]], Optional[str]
]:
    """Load the given meta-model from the file system and understand it."""
    text = model_path.read_text(encoding="utf-8")

    atok, parse_exception = parse.source_to_atok(source=text)
    if parse_exception:
        if isinstance(parse_exception, SyntaxError):
            return None, (
                f"Failed to parse the meta-model: "
                f"invalid syntax at line {parse_exception.lineno}"
            )
        else:
            return None, f"Failed to parse the meta-model: {parse_exception}"

    assert atok is not None

    import_errors = parse.check_expected_imports(atok=atok)
    if import_errors:
        writer = io.StringIO()
        write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=writer,
        )
        return None, writer.getvalue()

    lineno_columner = LinenoColumner(atok=atok)

    parsed_symbol_table, error = parse.atok_to_symbol_table(atok=atok)
    if error is not None:
        writer = io.StringIO()
        write_error_report(
            message="Failed to construct the symbol table",
            errors=[lineno_columner.error_message(error)],
            stderr=writer,
        )
        return None, writer.getvalue()

    assert parsed_symbol_table is not None

    ir_symbol_table, error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        atok=atok,
    )
    if error is not None:
        writer = io.StringIO()
        write_error_report(
            message=(
                "Failed to translate the parsed symbol table "
                "to intermediate symbol table"
            ),
            errors=[lineno_columner.error_message(error)],
            stderr=writer,
        )
        return None, writer.getvalue()

    assert ir_symbol_table is not None

    return (ir_symbol_table, atok), None
