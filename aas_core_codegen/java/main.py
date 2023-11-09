"""Generate Java code to handle asset administration shells based on the meta-model."""
from typing import TextIO

from aas_core_codegen import specific_implementations, run
from aas_core_codegen.java import (
    common as java_common,
    structure as java_structure,
)

def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""

    verified_ir_table, errors = java_structure.verify(
        symbol_table=context.symbol_table
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to verify the intermediate symbol table "
            f"for generation of C# code"
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert verified_ir_table is not None

    _ = context
    _ = stderr

    package_key = specific_implementations.ImplementationKey("package.txt")
    package_text = context.spec_impls.get(package_key, None)
    if package_text is None:
        stderr.write(f"The namespace snippet is missing: {package_key}\n")
        return 1

    if not java_common.PACKAGE_IDENTIFIER_RE.fullmatch(package_text):
        stderr.write(
            f"The text from the snippet {package_key} "
            f"is not a valid namespace identifier: {package_text!r}\n"
        )
        return 1

    package = java_common.PackageIdentifier(package_text)

    # region Structure

    code, errors = java_structure.generate(
        symbol_table=verified_ir_table,
        package=package,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the structures in the Java code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "types.java"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the Java structures to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
