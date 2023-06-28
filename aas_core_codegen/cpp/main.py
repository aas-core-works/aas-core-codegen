"""Generate C++ code to handle models based on the meta-model."""
from typing import TextIO

from aas_core_codegen import run, intermediate, specific_implementations
from aas_core_codegen.common import Stripped
from aas_core_codegen.cpp import (
    aas_common as cpp_aas_common,
    constants as cpp_constants,
    enhancing as cpp_enhancing,
    iteration as cpp_iteration,
    jsonization as cpp_jsonization,
    stringification as cpp_stringification,
    structure as cpp_structure,
    verification as cpp_verification,
    visitation as cpp_visitation,
    xmlization as cpp_xmlization,
    wstringification as cpp_wstringification,
)


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    verified_ir_table, errors = cpp_structure.verify(symbol_table=context.symbol_table)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to verify the intermediate symbol table "
            f"for generation of C++ code"
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

    # region Namespace

    namespace_key = specific_implementations.ImplementationKey("namespace.txt")
    namespace_text = context.spec_impls.get(namespace_key, None)
    if namespace_text is None:
        stderr.write(f"The namespace snippet is missing: {namespace_key}\n")
        return 1

    namespace = Stripped(namespace_text.strip())

    # endregion

    try:
        context.output_dir.mkdir(exist_ok=True, parents=True)
    except Exception as exception:
        stderr.write(
            f"Failed to create the output directory {context.output_dir}: {exception}"
        )
        return 1

    # region Common
    pth = context.output_dir / "common.hpp"
    try:
        pth.write_text(
            cpp_aas_common.generate_header(library_namespace=namespace),
            encoding="utf-8",
        )
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the header of the common C++ code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    pth = context.output_dir / "common.cpp"
    try:
        pth.write_text(
            cpp_aas_common.generate_implementation(library_namespace=namespace),
            encoding="utf-8",
        )
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the common C++ code to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Constants
    code, errors = cpp_constants.generate_header(
        symbol_table=context.symbol_table, library_namespace=namespace
    )

    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the header for the constants in the C++ "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "constants.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the header for the constants in the C++ to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    code, errors = cpp_constants.generate_implementation(
        symbol_table=context.symbol_table, library_namespace=namespace
    )

    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the implementation of the constants in the C++ "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "constants.cpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of constants in the C++ to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Enhancing
    code, errors = cpp_enhancing.generate_header(
        symbol_table=context.symbol_table, library_namespace=namespace
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the header of the enhancing C++ code "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "enhancing.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the header of the enhancing C++ code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Iteration
    code, errors = cpp_iteration.generate_header(
        symbol_table=context.symbol_table, library_namespace=namespace
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the header of the C++ iteration "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    pth = context.output_dir / "iteration.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the header of the iteration C++ code " f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    code, errors = cpp_iteration.generate_implementation(
        symbol_table=context.symbol_table, library_namespace=namespace
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the implementation of the C++ iteration "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "iteration.cpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the C++ iteration " f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Jsonization
    code = cpp_jsonization.generate_header(
        symbol_table=verified_ir_table, library_namespace=namespace
    )

    pth = context.output_dir / "jsonization.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the header for the C++ jsonization code " f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    code, errors = cpp_jsonization.generate_implementation(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        library_namespace=namespace,
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the implementation of the C++ jsonization code "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "jsonization.cpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the C++ jsonization code "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Stringification
    code = cpp_stringification.generate_header(
        symbol_table=context.symbol_table, library_namespace=namespace
    )

    pth = context.output_dir / "stringification.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the header of the stringification C++ code "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    code = cpp_stringification.generate_implementation(
        symbol_table=context.symbol_table, library_namespace=namespace
    )

    pth = context.output_dir / "stringification.cpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the stringification C++ code "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Types
    code, errors = cpp_structure.generate_header(
        symbol_table=verified_ir_table,
        spec_impls=context.spec_impls,
        library_namespace=namespace,
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the header for the C++ data structures "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "types.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the header for the C++ data structures " f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    code, errors = cpp_structure.generate_implementation(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        library_namespace=namespace,
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the implementation of the C++ data structures "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "types.cpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the C++ data structures "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Verification
    code, errors = cpp_verification.generate_header(
        symbol_table=verified_ir_table,
        spec_impls=context.spec_impls,
        library_namespace=namespace,
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the header for the C++ verification code "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "verification.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the header for the C++ verification code " f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    code, errors = cpp_verification.generate_implementation(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        library_namespace=namespace,
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the implementation of the C++ verification code "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "verification.cpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the C++ verification code "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Visitation
    pth = context.output_dir / "visitation.hpp"
    try:
        pth.write_text(
            cpp_visitation.generate_header(
                symbol_table=verified_ir_table, library_namespace=namespace
            ),
            encoding="utf-8",
        )
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the header of the visitation C++ code to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    pth = context.output_dir / "visitation.cpp"
    try:
        pth.write_text(
            cpp_visitation.generate_implementation(
                symbol_table=verified_ir_table, library_namespace=namespace
            ),
            encoding="utf-8",
        )
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the visitation C++ code "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Xmlization
    code = cpp_xmlization.generate_header(
        symbol_table=verified_ir_table, library_namespace=namespace
    )

    pth = context.output_dir / "xmlization.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the header for the C++ xmlization code " f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    code, errors = cpp_xmlization.generate_implementation(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        library_namespace=namespace,
    )
    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the implementation of the C++ xmlization code "
                f"based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in
                    errors],
            stderr=stderr,
        )
        return 1
    assert code is not None

    pth = context.output_dir / "xmlization.cpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the C++ xmlization code "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    # region Wstringification
    code = cpp_wstringification.generate_header(
        symbol_table=context.symbol_table, library_namespace=namespace
    )

    pth = context.output_dir / "wstringification.hpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the header of the wstringification C++ code "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    code = cpp_wstringification.generate_implementation(
        symbol_table=context.symbol_table, library_namespace=namespace
    )

    pth = context.output_dir / "wstringification.cpp"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=(
                f"Failed to write the implementation of the wstringification C++ code "
                f"to {pth}"
            ),
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1
    # endregion

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
