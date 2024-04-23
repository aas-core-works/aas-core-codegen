"""Generate Python code to handle AAS models based on the meta-model."""
from typing import TextIO

from aas_core_codegen import specific_implementations, run, intermediate
from aas_core_codegen.python import (
    common as python_common,
    structure as python_structure,
    constants as python_constants,
    aas_common as python_aas_common,
    stringification as python_stringification,
    verification as python_verification,
    jsonization as python_jsonization,
    xmlization as python_xmlization,
)


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    verified_ir_table, errors = python_structure.verify(
        symbol_table=context.symbol_table
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to verify the intermediate symbol table "
            f"for generation of Python code"
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

    aas_module_key = specific_implementations.ImplementationKey(
        "qualified_module_name.txt"
    )

    aas_module_text = context.spec_impls.get(aas_module_key, None)
    if aas_module_text is None:
        stderr.write(
            f"The snippet with the qualified module name is missing: {aas_module_key}\n"
        )
        return 1

    if not python_common.QUALIFIED_MODULE_NAME_RE.fullmatch(aas_module_text):
        stderr.write(
            f"The text from the snippet {aas_module_key} "
            f"is not a valid qualified module name: {aas_module_text!r}\n"
        )
        return 1

    aas_module = python_common.QualifiedModuleName(aas_module_text)

    # region Structure

    code, errors = python_structure.generate(
        symbol_table=verified_ir_table,
        aas_module=aas_module,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the structures in the Python code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "types.py"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the Python structures to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Constants

    code, errors = python_constants.generate(
        symbol_table=context.symbol_table, aas_module=aas_module
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the constants in the Python code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "constants.py"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the constants in the Python code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Common

    code = python_aas_common.generate(aas_module=aas_module)

    pth = context.output_dir / "common.py"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the common Python code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Stringification

    code, errors = python_stringification.generate(
        symbol_table=context.symbol_table, aas_module=aas_module
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the stringification Python code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "stringification.py"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the stringification Python code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Verification

    verify_errors = python_verification.verify(
        spec_impls=context.spec_impls,
        verification_functions=verified_ir_table.verification_functions,
    )

    if verify_errors is not None:
        run.write_error_report(
            message="Failed to verify the Python-specific structures",
            errors=verify_errors,
            stderr=stderr,
        )
        return 1

    code, errors = python_verification.generate(
        symbol_table=verified_ir_table,
        aas_module=aas_module,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the verification Python code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "verification.py"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the verification Python code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Jsonization

    code, errors = python_jsonization.generate(
        symbol_table=context.symbol_table,
        aas_module=aas_module,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the jsonization Python code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "jsonization.py"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the jsonization Python code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Xmlization

    code, errors = python_xmlization.generate(
        symbol_table=context.symbol_table,
        aas_module=aas_module,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the xmlization Python code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "xmlization.py"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the xmlization Python code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
