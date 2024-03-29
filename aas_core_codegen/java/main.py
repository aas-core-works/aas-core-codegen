"""Generate Java code to handle asset administration shells based on the meta-model."""
from typing import TextIO

from aas_core_codegen import specific_implementations, run
from aas_core_codegen.java import (
    common as java_common,
    constants as java_constants,
    copying as java_copying,
    enhancing as java_enhancing,
    generation as java_generation,
    jsonization as java_jsonization,
    reporting as java_reporting,
    stringification as java_stringification,
    structure as java_structure,
    verification as java_verification,
    visitation as java_visitation,
    xmlization as java_xmlization,
)


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""

    verified_ir_table, errors = java_structure.verify(symbol_table=context.symbol_table)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to verify the intermediate symbol table "
            f"for generation of Java code"
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

    source_files, errors = java_structure.generate(
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

    assert source_files is not None

    (context.output_dir / "types" / java_common.CLASS_PKG).mkdir(
        exist_ok=True, parents=True
    )
    (context.output_dir / "types" / java_common.INTERFACE_PKG).mkdir(
        exist_ok=True, parents=True
    )
    (context.output_dir / "types" / java_common.ENUM_PKG).mkdir(
        exist_ok=True, parents=True
    )

    for source_file in source_files:
        pth = context.output_dir / "types" / source_file.name
        try:
            pth.write_text(source_file.content, encoding="utf-8")
        except Exception as exception:
            run.write_error_report(
                message=f"Failed to write the Java structures to {pth}",
                errors=[str(exception)],
                stderr=stderr,
            )
            return 1

    # endregion

    # region Visitation

    source_files, errors = java_visitation.generate(
        symbol_table=context.symbol_table, package=package
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the Java code for visitation "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert source_files is not None

    (context.output_dir / "visitation").mkdir(exist_ok=True, parents=True)

    for source_file in source_files:
        pth = context.output_dir / "visitation" / source_file.name
        try:
            pth.write_text(source_file.content, encoding="utf-8")
        except Exception as exception:
            run.write_error_report(
                message=f"Failed to write the visitation Java code to {pth}",
                errors=[str(exception)],
                stderr=stderr,
            )
            return 1

    # endregion

    # region Constants

    code, errors = java_constants.generate(
        symbol_table=context.symbol_table,
        package=package,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the constants in the Java code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "constants" / "Constants.java"
    pth.parent.mkdir(exist_ok=True, parents=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the constants in the Java code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Verification

    verify_errors = java_verification.verify(
        spec_impls=context.spec_impls,
        verification_functions=verified_ir_table.verification_functions,
    )

    if verify_errors is not None:
        run.write_error_report(
            message="Failed to verify for generation of Java verification code",
            errors=verify_errors,
            stderr=stderr,
        )
        return 1

    code, errors = java_verification.generate(
        symbol_table=verified_ir_table,
        package=package,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the verification Java code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "verification" / "Verification.java"
    pth.parent.mkdir(exist_ok=True, parents=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the verification Java code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Reporting

    code = java_reporting.generate(package=package)

    pth = context.output_dir / "reporting" / "Reporting.java"
    pth.parent.mkdir(exist_ok=True, parents=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the reporting Java code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Stringification

    code, errors = java_stringification.generate(
        symbol_table=context.symbol_table, package=package
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the stringification Java code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "stringification" / "Stringification.java"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the stringification Java code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Xmlization

    code, errors = java_xmlization.generate(
        symbol_table=context.symbol_table,
        package=package,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the xmlization Java code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "xmlization" / "Xmlization.java"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the xmlization Java code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Jsonization

    code, errors = java_jsonization.generate(
        symbol_table=context.symbol_table,
        package=package,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the jsonization Java code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "jsonization" / "Jsonization.java"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the jsonization Java code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Copying

    code, errors = java_copying.generate(
        symbol_table=context.symbol_table,
        package=package,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the Java code for shallow and deep copying "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "copying" / "Copying.java"
    pth.parent.mkdir(exist_ok=True, parents=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the Java code for shallow and deep copying "
            f"to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Enhancing

    source_files, errors = java_enhancing.generate(
        symbol_table=context.symbol_table,
        package=package,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the Java code for enhancing "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert source_files is not None

    (context.output_dir / "enhancing").mkdir(exist_ok=True, parents=True)

    for source_file in source_files:
        pth = context.output_dir / "enhancing" / source_file.name

        try:
            pth.write_text(source_file.content, encoding="utf-8")
        except Exception as exception:
            run.write_error_report(
                message=f"Failed to write the Java code for enhancing to {pth}",
                errors=[str(exception)],
                stderr=stderr,
            )
            return 1

    # endregion

    # region Generation

    source_files, errors = java_generation.generate(
        symbol_table=context.symbol_table,
        package=package,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the Java code for generation "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert source_files is not None

    (context.output_dir / "generation").mkdir(exist_ok=True, parents=True)

    for source_file in source_files:
        pth = context.output_dir / "generation" / source_file.name

        try:
            pth.write_text(source_file.content, encoding="utf-8")
        except Exception as exception:
            run.write_error_report(
                message=f"Failed to write the Java code for generation to {pth}",
                errors=[str(exception)],
                stderr=stderr,
            )
            return 1

    # endregion

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
