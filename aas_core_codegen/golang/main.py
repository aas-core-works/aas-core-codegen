"""Generate Golang code to handle AAS models based on the meta-model."""
from typing import TextIO

from aas_core_codegen import run, intermediate, specific_implementations
from aas_core_codegen.common import Stripped
from aas_core_codegen.golang import (
    aas_common as golang_aas_common,
    constants as golang_constants,
    enhancing as golang_enhancing,
    jsonization as golang_jsonization,
    reporting as golang_reporting,
    stringification as golang_stringification,
    structure as golang_structure,
    verification as golang_verification,
    xmlization as golang_xmlization,
)


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    verified_ir_table, errors = golang_structure.verify(
        symbol_table=context.symbol_table
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to verify the intermediate symbol table "
            f"for generation of Golang code"
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

    # region Repo URL

    repo_url_key = specific_implementations.ImplementationKey("repo_url.txt")
    repo_url_text = context.spec_impls.get(repo_url_key, None)
    if repo_url_text is None:
        stderr.write(f"The repo URL snippet is missing: {repo_url_key}\n")
        return 1

    repo_url = Stripped(repo_url_text.strip())

    # endregion

    # region Common
    pth = context.output_dir / "common/common.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(golang_aas_common.generate(), encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the common Golang code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Constants

    code, errors = golang_constants.generate(
        symbol_table=context.symbol_table, repo_url=repo_url
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the constants in the Golang code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "constants/constants.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the constants in the Golang code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Enhancing

    code, errors = golang_enhancing.generate(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        repo_url=repo_url,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the enhancing Golang code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "enhancing/enhancing.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the enhancing Golang code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Jsonization

    code, errors = golang_jsonization.generate(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        repo_url=repo_url,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the jsonization Golang code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "jsonization/jsonization.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the jsonization Golang code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Reporting

    code = golang_reporting.generate()

    pth = context.output_dir / "reporting/reporting.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the reporting Golang code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Stringification

    code, errors = golang_stringification.generate(
        symbol_table=context.symbol_table, repo_url=repo_url
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the stringification Golang code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "stringification/stringification.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the stringification Golang code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Structure

    code, errors = golang_structure.generate(
        symbol_table=verified_ir_table,
        spec_impls=context.spec_impls,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the structures in the Golang code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "types/types.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the Golang structures to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Verification

    verify_errors = golang_verification.verify(
        spec_impls=context.spec_impls,
        verification_functions=verified_ir_table.verification_functions,
    )

    if verify_errors is not None:
        run.write_error_report(
            message="Failed to verify for the generation of Golang verification code",
            errors=verify_errors,
            stderr=stderr,
        )
        return 1

    code, errors = golang_verification.generate(
        symbol_table=verified_ir_table, spec_impls=context.spec_impls, repo_url=repo_url
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the verification Golang code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "verification/verification.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the verification Golang code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region Xmlization

    code, errors = golang_xmlization.generate(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        repo_url=repo_url,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the xmlization Golang code "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "xmlization/xmlization.go"
    pth.parent.mkdir(exist_ok=True)

    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the xmlization Golang code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
