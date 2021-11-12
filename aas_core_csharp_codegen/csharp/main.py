"""Generate C# code to handle asset administration shells based on the meta-model."""
import argparse
import pathlib
import sys
from typing import TextIO

import aas_core_csharp_codegen
from aas_core_csharp_codegen import cli, parse, intermediate, specific_implementations
from aas_core_csharp_codegen.common import LinenoColumner
from aas_core_csharp_codegen.csharp import (
    common as csharp_common,
    structure as csharp_structure,
    visitation as csharp_visitation,
    verification as csharp_verification,
    stringification as csharp_stringification,
    jsonization as csharp_jsonization,
    xmlization as csharp_xmlization
)

assert aas_core_csharp_codegen.__doc__ == __doc__


class Parameters:
    """Represent the program parameters."""

    def __init__(
            self,
            model_path: pathlib.Path,
            snippets_dir: pathlib.Path,
            output_dir: pathlib.Path
    ) -> None:
        """Initialize with the given values."""
        self.model_path = model_path
        self.snippets_dir = snippets_dir
        self.output_dir = output_dir


def run(params: Parameters, stdout: TextIO, stderr: TextIO) -> int:
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
        if not params.snippets_dir.is_dir():
            stderr.write(
                f"The --output_dir does not point to a directory: "
                f"{params.output_dir}\n")
            return 1

    # endregion

    spec_impls, spec_impls_errors = specific_implementations.read_from_directory(
        snippets_dir=params.snippets_dir)
    if spec_impls_errors:
        cli.write_error_report(
            message="Failed to resolve the implementation-specific code snippets",
            errors=spec_impls_errors,
            stderr=stderr)
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
        cli.write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=stderr,
        )

        return 1

    lineno_columner = LinenoColumner(atok=atok)

    parsed_symbol_table, error = parse.atok_to_symbol_table(atok=atok)
    if error is not None:
        cli.write_error_report(
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
        cli.write_error_report(
            message=f"Failed to translate the parsed symbol table "
                    f"to intermediate symbol table "
                    f"based on {params.model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    verified_ir_table, errors = csharp_structure.verify(
        symbol_table=ir_symbol_table)

    if errors is not None:
        cli.write_error_report(
            message=f"Failed to verify the intermediate symbol table "
                    f"for generation of C# code"
                    f"based on {params.model_path}",
            errors=[
                lineno_columner.error_message(error)
                for error in errors
            ],
            stderr=stderr)
        return 1

    namespace_key = specific_implementations.ImplementationKey("namespace.txt")
    namespace_text = spec_impls.get(namespace_key, None)
    if namespace_text is None:
        stderr.write(
            f"The namespace snippet is missing: {namespace_key}\n"
        )
        return 1

    if not csharp_common.NAMESPACE_IDENTIFIER_RE.fullmatch(namespace_text):
        stderr.write(
            f"The text from the snippet {namespace_key} "
            f"is not a valid namespace identifier: {namespace_text!r}\n"
        )
        return 1

    namespace = csharp_common.NamespaceIdentifier(namespace_text)

    # region Structure

    code, errors = csharp_structure.generate(
        symbol_table=verified_ir_table,
        namespace=namespace,
        spec_impls=spec_impls)

    if errors is not None:
        cli.write_error_report(
            message=f"Failed to _generate_rdf the structures in the C# code "
                    f"based on {params.model_path}",
            errors=[lineno_columner.error_message(error) for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = params.output_dir / "types.cs"
    try:
        pth.write_text(code)
    except Exception as exception:
        cli.write_error_report(
            message=f"Failed to write the C# structures to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    # region Visitation

    code, errors = csharp_visitation.generate(
        symbol_table=ir_symbol_table,
        namespace=namespace)

    if errors is not None:
        cli.write_error_report(
            message=f"Failed to _generate_rdf the C# code for visitation "
                    f"based on {params.model_path}",
            errors=[
                lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = params.output_dir / "visitation.cs"
    try:
        pth.write_text(code)
    except Exception as exception:
        cli.write_error_report(
            message=f"Failed to write the visitation C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    # region Verification

    errors = csharp_verification.verify(spec_impls=spec_impls)
    if errors is not None:
        cli.write_error_report(
            message=f"Failed to verify the C#-specific C# structures",
            errors=errors,
            stderr=stderr)
        return 1

    code, errors = csharp_verification.generate(
        symbol_table=verified_ir_table,
        namespace=namespace,
        spec_impls=spec_impls)

    if errors is not None:
        cli.write_error_report(
            message=f"Failed to _generate_rdf the verification C# code "
                    f"based on {params.model_path}",
            errors=[
                lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = params.output_dir / "verification.cs"
    try:
        pth.write_text(code)
    except Exception as exception:
        cli.write_error_report(
            message=f"Failed to write the verification C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    # region Stringification

    code, errors = csharp_stringification.generate(
        symbol_table=ir_symbol_table, namespace=namespace)

    if errors is not None:
        cli.write_error_report(
            message=f"Failed to _generate_rdf the stringification C# code "
                    f"based on {params.model_path}",
            errors=[
                lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = params.output_dir / "stringification.cs"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code)
    except Exception as exception:
        cli.write_error_report(
            message=f"Failed to write the stringification C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    interface_implementers = intermediate.map_interface_implementers(
        symbol_table=ir_symbol_table)

    # region Jsonization

    code, errors = csharp_jsonization.generate(
        symbol_table=ir_symbol_table,
        namespace=namespace,
        interface_implementers=interface_implementers,
        spec_impls=spec_impls)

    if errors is not None:
        cli.write_error_report(
            message=f"Failed to _generate_rdf the jsonization C# code "
                    f"based on {params.model_path}",
            errors=[
                lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = params.output_dir / "jsonization.cs"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code)
    except Exception as exception:
        cli.write_error_report(
            message=f"Failed to write the jsonization C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    # region Xmlization

    code, errors = csharp_xmlization.generate(
        symbol_table=ir_symbol_table,
        namespace=namespace,
        interface_implementers=interface_implementers,
        spec_impls=spec_impls)

    if errors is not None:
        cli.write_error_report(
            message=f"Failed to _generate_rdf the xmlization C# code "
                    f"based on {params.model_path}",
            errors=[
                lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = params.output_dir / "xmlization.cs"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code)
    except Exception as exception:
        cli.write_error_report(
            message=f"Failed to write the xmlization C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

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
    args = parser.parse_args()

    params = Parameters(
        model_path=pathlib.Path(args.model_path),
        snippets_dir=pathlib.Path(args.snippets_dir),
        output_dir=pathlib.Path(args.output_dir),
    )

    run(params=params, stdout=sys.stdout, stderr=sys.stderr)

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="aas-core-csharp-codegen")


if __name__ == "__main__":
    sys.exit(main("aas-core-csharp-codegen"))
