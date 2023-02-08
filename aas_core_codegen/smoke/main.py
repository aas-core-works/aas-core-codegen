"""Run a smoke-test as a preliminary test that a meta-model is ready for generation."""

import argparse
import pathlib
import sys
from typing import TextIO, List, MutableMapping

import aas_core_codegen
import aas_core_codegen.smoke
from aas_core_codegen import (
    parse,
    run,
    intermediate,
    infer_for_schema,
    specific_implementations,
)
from aas_core_codegen.common import LinenoColumner, Error, Stripped
from aas_core_codegen.csharp import common as csharp_common
from aas_core_codegen.csharp.structure import (
    _generate as csharp_structure_generate,
)
from aas_core_codegen.csharp.verification import (
    _generate as csharp_verification_generate,
)

assert __doc__ == aas_core_codegen.smoke.__doc__


def _smoke_transpile_to_csharp(symbol_table: intermediate.SymbolTable) -> List[Error]:
    """Try to transpile to C# what you can without snippets."""
    # fmt: off
    verified_symbol_table, structure_verification_errors = (
        csharp_structure_generate.verify(
            symbol_table
        )
    )
    # fmt: on
    if structure_verification_errors is not None:
        return structure_verification_errors

    assert verified_symbol_table is not None

    errors = []

    spec_impls = (
        dict()
    )  # type: MutableMapping[specific_implementations.ImplementationKey, Stripped]

    dummy_implementation = Stripped("DUMMY IMPLEMENTATION")

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.Class):
            continue

        if our_type.is_implementation_specific:
            key = specific_implementations.ImplementationKey(
                "Types/{our_type.name}/{our_type.name}.cs"
            )
            spec_impls[key] = dummy_implementation
            continue

        for method in our_type.methods:
            if isinstance(method, intermediate.ImplementationSpecificMethod):
                key = specific_implementations.ImplementationKey(
                    f"Types/{our_type.name}/{method.name}.cs"
                )
                spec_impls[key] = dummy_implementation

    for verification in symbol_table.verification_functions:
        if isinstance(verification, intermediate.ImplementationSpecificVerification):
            key = specific_implementations.ImplementationKey(
                f"Verification/{verification.name}.cs"
            )
            spec_impls[key] = dummy_implementation

    namespace = csharp_common.NamespaceIdentifier("DummyNamespace")

    _, structure_errors = csharp_structure_generate.generate(
        symbol_table=verified_symbol_table, namespace=namespace, spec_impls=spec_impls
    )
    if structure_errors is not None:
        errors.extend(structure_errors)

    _, verification_errors = csharp_verification_generate.generate(
        symbol_table=symbol_table, namespace=namespace, spec_impls=spec_impls
    )
    if verification_errors is not None:
        errors.extend(verification_errors)

    return errors


def execute(model_path: pathlib.Path, stderr: TextIO) -> int:
    """Run the smoke test."""
    text = model_path.read_text(encoding="utf-8")

    # BEFORE-RELEASE (mristin, 2021-12-13):
    #  test all the following individual failure cases
    atok, parse_exception = parse.source_to_atok(source=text)
    if parse_exception:
        if isinstance(parse_exception, SyntaxError):
            stderr.write(
                f"Failed to parse the meta-model {model_path}: "
                f"invalid syntax at line {parse_exception.lineno}\n"
            )
        else:
            stderr.write(
                f"Failed to parse the meta-model {model_path}: {parse_exception}\n"
            )

        return 1

    assert atok is not None

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
            message=f"Failed to construct the symbol table from {model_path}",
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
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    assert ir_symbol_table is not None

    constraints_by_class, errors = infer_for_schema.infer_constraints_by_class(
        symbol_table=ir_symbol_table
    )
    if errors is not None:
        run.write_error_report(
            message=f"Failed to infer the constraints by class for the schemas "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )

        return 1

    assert constraints_by_class is not None

    _, error = infer_for_schema.merge_constraints_with_ancestors(
        symbol_table=ir_symbol_table, constraints_by_class=constraints_by_class
    )
    if errors is not None:
        run.write_error_report(
            message=f"Failed to merge the constraints with ancestors for the schemas "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    errors = _smoke_transpile_to_csharp(symbol_table=ir_symbol_table)

    if len(errors) > 0:
        run.write_error_report(
            message=f"Failed to smoke-transpile what we could without snippets to C# "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )

        return 1

    return 0


def main(prog: str) -> int:
    """Execute the main routine."""
    # NOTE (mristin, 2022-03-28):
    # The module ``argparse`` is not flexible enough to understand special options such
    # as ``--version`` so we manually hard-wire.
    if "--version" in sys.argv and "--help" not in sys.argv:
        print(aas_core_codegen.__version__)
        return 0

    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument("--model_path", help="path to the meta-model", required=True)
    parser.add_argument(
        "--version", help="show the current version and exit", action="store_true"
    )
    args = parser.parse_args()

    return execute(model_path=pathlib.Path(args.model_path), stderr=sys.stderr)


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="aas-core-codegen-smoke")


if __name__ == "__main__":
    sys.exit(main(prog="aas-core-codegen-smoke"))
