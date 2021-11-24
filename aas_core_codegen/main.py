"""Generate different implementations and schemas based on an AAS meta-model."""

import argparse
import enum
import pathlib
import sys
from typing import TextIO

import aas_core_codegen
from aas_core_codegen import (
    parse, run, specific_implementations, intermediate
)
from aas_core_codegen.common import LinenoColumner, assert_never

assert aas_core_codegen.__doc__ == __doc__


class Target(enum.Enum):
    CSHARP = "csharp"
    JSONSCHEMA = "jsonschema"
    RDF_SHACL = "rdf-shacl"
    XSD = "xsd"


class Parameters:
    """Represent the program parameters."""

    def __init__(
            self,
            model_path: pathlib.Path,
            target: Target,
            snippets_dir: pathlib.Path,
            output_dir: pathlib.Path
    ) -> None:
        """Initialize with the given values."""
        self.model_path = model_path
        self.target = target
        self.snippets_dir = snippets_dir
        self.output_dir = output_dir


def execute(params: Parameters, stdout: TextIO, stderr: TextIO) -> int:
    """Run the program."""
    # region Basic checks
    # TODO: test this failure case
    if not params.model_path.exists():
        stderr.write(f"The --model_path does not exist: {params.model_path}\n")
        return 1

    # TODO: test this failure case
    if not params.model_path.is_file():
        stderr.write(
            f"The --model_path does not point to a file: {params.model_path}\n")
        return 1

    # TODO: test this failure case
    if not params.snippets_dir.exists():
        stderr.write(f"The --snippets_dir does not exist: {params.snippets_dir}\n")
        return 1

    # TODO: test this failure case
    if not params.snippets_dir.is_dir():
        stderr.write(
            f"The --snippets_dir does not point to a directory: "
            f"{params.snippets_dir}\n")
        return 1

    # TODO: test the happy path
    if not params.output_dir.exists():
        params.output_dir.mkdir(parents=True, exist_ok=True)
    else:
        # TODO: test this failure case
        if not params.output_dir.is_dir():
            stderr.write(
                f"The --output_dir does not point to a directory: "
                f"{params.output_dir}\n")
            return 1

    # endregion

    # region Parse

    spec_impls, spec_impls_errors = (
        specific_implementations.read_from_directory(
            snippets_dir=params.snippets_dir))

    if spec_impls_errors:
        run.write_error_report(
            message="Failed to resolve the implementation-specific "
                    "JSON schema snippets",
            errors=spec_impls_errors,
            stderr=stderr)
        return 1

    text = params.model_path.read_text(encoding='utf-8')

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
        run.write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=stderr,
        )

        return 1

    lineno_columner = LinenoColumner(atok=atok)

    parsed_symbol_table, error = parse.atok_to_symbol_table(atok=atok)
    if error is not None:
        run.write_error_report(
            message=f"Failed to construct the symbol table from {params.model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    assert parsed_symbol_table is not None

    ir_symbol_table, error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        atok=atok,
    )
    if error is not None:
        run.write_error_report(
            message=f"Failed to translate the parsed symbol table "
                    f"to intermediate symbol table "
                    f"based on {params.model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    interface_implementers = intermediate.map_interface_implementers(
        symbol_table=ir_symbol_table)

    # endregion

    # region Dispatch

    run_context = run.Context(
        model_path=params.model_path,
        symbol_table=ir_symbol_table,
        spec_impls=spec_impls,
        interface_implementers=interface_implementers,
        lineno_columner=lineno_columner,
        output_dir=params.output_dir)

    # NOTE (mristin, 2021-11-24):
    # Import the individual modules only if necessary to optimize for the start-up time.
    # Additionally, bugs in the individual modules still allow us to run the other
    # modules.

    if params.target == Target.CSHARP:
        import aas_core_codegen.csharp.main as csharp_main
        return csharp_main.execute(context=run_context, stdout=stdout, stderr=stderr)

    elif params.target == Target.JSONSCHEMA:
        import aas_core_codegen.jsonschema.main as jsonschema_main
        return jsonschema_main.execute(context=run_context, stdout=stdout, stderr=stderr)

    elif params.target == Target.RDF_SHACL:
        import aas_core_codegen.rdf_shacl.main as rdf_shacl_main
        return rdf_shacl_main.execute(context=run_context, stdout=stdout, stderr=stderr)

    elif params.target == Target.XSD:
        import aas_core_codegen.xsd.main as xsd_main
        return xsd_main.execute(context=run_context, stdout=stdout, stderr=stderr)

    else:
        assert_never(params.target)

    # endregion

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
        "--snippets_dir",
        help="path to the directory containing implementation-specific code snippets",
        required=True)
    parser.add_argument(
        "--output_dir", help="path to the generated code", required=True
    )
    parser.add_argument(
        "--target", help="target language or schema", required=True,
        choices=[literal.value for literal in Target]
    )
    args = parser.parse_args()

    target_to_str = {literal.value: literal for literal in Target}

    params = Parameters(
        model_path=pathlib.Path(args.model_path),
        target=target_to_str[args.target],
        snippets_dir=pathlib.Path(args.snippets_dir),
        output_dir=pathlib.Path(args.output_dir)
    )

    return execute(params=params, stdout=sys.stdout, stderr=sys.stderr)


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="aas-core-codegen")


if __name__ == "__main__":
    sys.exit(main("aas-core-codegen"))
