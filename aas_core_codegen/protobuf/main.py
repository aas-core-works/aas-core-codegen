"""Generate ProtoBuf code to handle asset administration shells based on the meta-model."""

from typing import TextIO

from aas_core_codegen import specific_implementations, run, intermediate
from aas_core_codegen.protobuf import (
    common as proto_common,
    constants as proto_constants,
    structure as proto_structure,
)


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    verified_ir_table, errors = proto_structure.verify(
        symbol_table=context.symbol_table
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to verify the intermediate symbol table "
            f"for generation of ProtoBuf code"
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert verified_ir_table is not None

    unsupported_contracts_errors = (
        intermediate.errors_if_contracts_for_functions_or_methods_defined(
            verified_ir_table
        )
    )
    if unsupported_contracts_errors is not None:
        run.write_error_report(
            message=f"We do not support pre and post-conditions and snapshots "
            f"at the moment. Please notify the developers if you need this "
            f"feature (based on meta-model {context.model_path})",
            errors=[
                context.lineno_columner.error_message(error)
                for error in unsupported_contracts_errors
            ],
            stderr=stderr,
        )
        return 1

    unsupported_methods_errors = (
        intermediate.errors_if_non_implementation_specific_methods(verified_ir_table)
    )
    if unsupported_methods_errors is not None:
        run.write_error_report(
            message=f"We added some support for understood methods already and keep "
            f"maintaining it as it is only a matter of time when we will "
            f"introduce their transpilation. Introducing them after the fact "
            f"would have been much more difficult.\n"
            f"\n"
            f"At the given moment, however, we deliberately focus only on "
            f"implementation-specific methods. "
            f"(based on meta-model {context.model_path})",
            errors=[
                context.lineno_columner.error_message(error)
                for error in unsupported_methods_errors
            ],
            stderr=stderr,
        )
        return 1

    namespace_key = specific_implementations.ImplementationKey("namespace.txt")
    namespace_text = context.spec_impls.get(namespace_key, None)
    if namespace_text is None:
        stderr.write(f"The namespace snippet is missing: {namespace_key}\n")
        return 1

    if not proto_common.NAMESPACE_IDENTIFIER_RE.fullmatch(namespace_text):
        stderr.write(
            f"The text from the snippet {namespace_key} "
            f"is not a valid namespace identifier: {namespace_text!r}\n"
        )
        return 1

    namespace = proto_common.NamespaceIdentifier(namespace_text)

    # region Structure

    code, errors = proto_structure.generate(
        symbol_table=verified_ir_table,
        namespace=namespace,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the structures in the ProtoBuf code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "types.proto"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the ProtoBuf structures to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Constants

    code, errors = proto_constants.generate(
        symbol_table=context.symbol_table,
        namespace=namespace,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the constants in the ProtoBuf code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "constants.proto"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the constants in the ProtoBuf code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
