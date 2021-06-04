"""Generate C# code to handle asset administration shells based on the meta-model."""
import argparse
import pathlib
import sys
import textwrap
from typing import TextIO, Sequence

from icontract import require

import aas_core_csharp_codegen
from aas_core_csharp_codegen import parse, intermediate
from aas_core_csharp_codegen.common import LinenoColumner
from aas_core_csharp_codegen.understand import (
    constructor as understand_constructor,
    hierarchy as understand_hierarchy,
)

assert aas_core_csharp_codegen.__doc__ == __doc__


class Parameters:
    """Represent the program parameters."""

    def __init__(self, model_path: pathlib.Path, output_dir: pathlib.Path) -> None:
        self.model_path = model_path
        self.output_dir = output_dir


# fmt: off
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


def run(params: Parameters, stdout: TextIO, stderr: TextIO) -> int:
    """Run the program."""
    # TODO: test this failure case
    if not params.model_path.exists():
        stderr.write(f"The model file does not exist: {params.model_path}\n")
        return 1

    # TODO: test this failure case
    if not params.model_path.is_file():
        stderr.write(f"The model path does not point to a file: {params.model_path}\n")
        return 1

    text = params.model_path.read_text()

    # TODO: test all the following individual failure cases
    atok, parse_exception = parse.source_to_atok(source=text)
    if parse_exception:
        if isinstance(parse_exception, SyntaxError):
            stderr.write(
                f"Failed to parse the meta-model {params.model_path}: "
                f"invalid syntax at line {parse_exception.lineno}\n"
            )
        else:
            stderr.write(
                f"Failed to parse the meta-model {params.model_path}: "
                f"{parse_exception}\n"
            )

        return 1

    import_errors = parse.check_expected_imports(atok=atok)
    if import_errors:
        write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=stderr,
        )

        return 1

    lineno_columner = LinenoColumner(atok=atok)

    parsed_symbol_table, parse_error = parse.atok_to_symbol_table(atok=atok)
    if parse_error is not None:
        write_error_report(
            message=f"Failed to construct the symbol table from {params.model_path}",
            errors=[lineno_columner.error_message(parse_error)],
            stderr=stderr,
        )

        return 1

    assert parsed_symbol_table is not None

    ontology, ontology_errors = understand_hierarchy.symbol_table_to_ontology(
        symbol_table=parsed_symbol_table
    )
    if ontology_errors:
        write_error_report(
            message=f"Failed to construct the ontology based on the symbol table "
            f"parsed from {params.model_path}",
            errors=[lineno_columner.error_message(error) for error in ontology_errors],
            stderr=stderr,
        )

        return 1

    constructor_table, constructor_error = understand_constructor.understand_all(
        symbol_table=parsed_symbol_table, atok=atok
    )
    if constructor_error is not None:
        write_error_report(
            message=f"Failed to understand the constructors "
            f"based on the symbol table parsed from {params.model_path}",
            errors=[lineno_columner.error_message(constructor_error)],
            stderr=stderr,
        )

        return 1

    assert ontology is not None
    assert constructor_table is not None

    ir_symbol_table, ir_error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        ontology=ontology,
        constructor_table=constructor_table,
        atok=atok,
    )
    if ir_error is not None:
        write_error_report(
            message=f"Failed to translate the parsed symbol table "
            f"to intermediate symbol table "
            f"based on {params.model_path}",
            errors=[lineno_columner.error_message(ir_error)],
            stderr=stderr,
        )

        return 1

    # TODO: implement further steps

    stdout.write(f"Code generated to: {params.output_dir}\n")
    return 0


def main(prog: str) -> int:
    """
    Execute the main routine.

    :param prog: name of the program to be displayed in the help
    :return: exit code
    """
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument("--model_path", help="path to the meta-model", required=True)
    parser.add_argument(
        "--output_dir", help="path to the generated code", required=True
    )
    args = parser.parse_args()

    params = Parameters(
        model_path=pathlib.Path(args.model_path),
        output_dir=pathlib.Path(args.output_dir),
    )

    run(params=params, stdout=sys.stdout, stderr=sys.stderr)

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="aas-core-csharp-codegen")


if __name__ == "__main__":
    sys.exit(main("aas-core-csharp-codegen"))
