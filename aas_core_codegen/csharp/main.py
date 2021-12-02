"""Generate C# code to handle asset administration shells based on the meta-model."""
from typing import TextIO

from aas_core_codegen import intermediate, specific_implementations, run
from aas_core_codegen.csharp import (
    common as csharp_common,
    structure as csharp_structure,
    visitation as csharp_visitation,
    verification as csharp_verification,
    stringification as csharp_stringification,
    jsonization as csharp_jsonization
)


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    verified_ir_table, errors = csharp_structure.verify(
        symbol_table=context.symbol_table)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to verify the intermediate symbol table "
                    f"for generation of C# code"
                    f"based on {context.model_path}",
            errors=[
                context.lineno_columner.error_message(error)
                for error in errors
            ],
            stderr=stderr)
        return 1

    namespace_key = specific_implementations.ImplementationKey("namespace.txt")
    namespace_text = context.spec_impls.get(namespace_key, None)
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
        spec_impls=context.spec_impls)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the structures in the C# code "
                    f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = context.output_dir / "types.cs"
    try:
        pth.write_text(code)
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the C# structures to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    # region Visitation

    code, errors = csharp_visitation.generate(
        symbol_table=context.symbol_table,
        namespace=namespace)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the C# code for visitation "
                    f"based on {context.model_path}",
            errors=[
                context.lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = context.output_dir / "visitation.cs"
    try:
        pth.write_text(code)
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the visitation C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    # region Verification

    errors = csharp_verification.verify(spec_impls=context.spec_impls)
    if errors is not None:
        run.write_error_report(
            message=f"Failed to verify the C#-specific C# structures",
            errors=errors,
            stderr=stderr)
        return 1

    code, errors = csharp_verification.generate(
        symbol_table=verified_ir_table,
        namespace=namespace,
        spec_impls=context.spec_impls)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the verification C# code "
                    f"based on {context.model_path}",
            errors=[
                context.lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = context.output_dir / "verification.cs"
    try:
        pth.write_text(code)
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the verification C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    # region Stringification

    code, errors = csharp_stringification.generate(
        symbol_table=context.symbol_table, namespace=namespace)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the stringification C# code "
                    f"based on {context.model_path}",
            errors=[
                context.lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = context.output_dir / "stringification.cs"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code)
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the stringification C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    interface_implementers = intermediate.map_interface_implementers(
        symbol_table=context.symbol_table)

    # region Jsonization

    code, errors = csharp_jsonization.generate(
        symbol_table=context.symbol_table,
        namespace=namespace,
        interface_implementers=interface_implementers,
        spec_impls=context.spec_impls)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the jsonization C# code "
                    f"based on {context.model_path}",
            errors=[
                context.lineno_columner.error_message(error)
                for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = context.output_dir / "jsonization.cs"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code)
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the jsonization C# code to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0