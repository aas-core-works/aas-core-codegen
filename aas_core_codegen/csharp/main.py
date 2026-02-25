"""Generate C# code to handle asset administration shells based on the meta-model."""
import pathlib
from typing import TextIO, Sequence, Tuple, Callable, Optional, List

from aas_core_codegen import specific_implementations, run, intermediate
from aas_core_codegen.common import Error
from aas_core_codegen.csharp import common as csharp_common, lib as csharp_lib


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    verified_ir_table, errors = csharp_lib.verify_for_types(
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

    if not csharp_common.NAMESPACE_IDENTIFIER_RE.fullmatch(namespace_text):
        stderr.write(
            f"The text from the snippet {namespace_key} "
            f"is not a valid namespace identifier: {namespace_text!r}\n"
        )
        return 1

    namespace = csharp_common.NamespaceIdentifier(namespace_text)

    verify_errors = csharp_lib.verify_for_verification(
        spec_impls=context.spec_impls,
        verification_functions=verified_ir_table.verification_functions,
    )

    if verify_errors is not None:
        run.write_error_report(
            message="Failed to verify the verification functions for code generation",
            errors=verify_errors,
            stderr=stderr,
        )
        return 1

    project_rel_path = pathlib.Path(namespace)
    assert not project_rel_path.is_absolute()

    rel_paths_generators: Sequence[
        Tuple[pathlib.Path, Callable[[], Tuple[Optional[str], Optional[List[Error]]]]]
    ] = [
        (
            project_rel_path / "constants.cs",
            lambda: csharp_lib.generate_constants(
                symbol_table=context.symbol_table, namespace=namespace
            ),
        ),
        (
            project_rel_path / "copying.cs",
            lambda: csharp_lib.generate_copying(
                symbol_table=context.symbol_table,
                namespace=namespace,
                spec_impls=context.spec_impls,
            ),
        ),
        (
            project_rel_path / "enhancing.cs",
            lambda: csharp_lib.generate_enhancing(
                symbol_table=context.symbol_table,
                namespace=namespace,
                spec_impls=context.spec_impls,
            ),
        ),
        (
            project_rel_path / "jsonization.cs",
            lambda: csharp_lib.generate_jsonization(
                symbol_table=context.symbol_table,
                namespace=namespace,
                spec_impls=context.spec_impls,
            ),
        ),
        (
            project_rel_path / "reporting.cs",
            lambda: (csharp_lib.generate_reporting(namespace=namespace), None),
        ),
        (
            project_rel_path / "stringification.cs",
            lambda: csharp_lib.generate_stringification(
                symbol_table=context.symbol_table, namespace=namespace
            ),
        ),
        (
            project_rel_path / "types.cs",
            lambda: csharp_lib.generate_types(
                symbol_table=verified_ir_table,
                namespace=namespace,
                spec_impls=context.spec_impls,
            ),
        ),
        (
            project_rel_path / "verification.cs",
            lambda: csharp_lib.generate_verification(
                symbol_table=verified_ir_table,
                namespace=namespace,
                spec_impls=context.spec_impls,
            ),
        ),
        (
            project_rel_path / "visitation.cs",
            lambda: csharp_lib.generate_visitation(
                symbol_table=context.symbol_table, namespace=namespace
            ),
        ),
        (
            project_rel_path / "xmlization.cs",
            lambda: csharp_lib.generate_xmlization(
                symbol_table=context.symbol_table,
                namespace=namespace,
                spec_impls=context.spec_impls,
            ),
        ),
    ]

    for rel_path, generator_func in rel_paths_generators:
        assert not rel_path.is_absolute()

        code, errors = generator_func()

        if errors is not None:
            run.write_error_report(
                message=f"Failed to generate {rel_path} "
                f"based on {context.model_path}",
                errors=[
                    context.lineno_columner.error_message(error) for error in errors
                ],
                stderr=stderr,
            )
            return 1

        assert code is not None

        pth = context.output_dir / rel_path

        try:
            pth.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exception:
            run.write_error_report(
                message=f"Failed to create the directory {pth.parent}",
                errors=[str(exception)],
                stderr=stderr,
            )
            return 1

        try:
            pth.write_text(code, encoding="utf-8")
        except Exception as exception:
            run.write_error_report(
                message=f"Failed to write to {pth}",
                errors=[str(exception)],
                stderr=stderr,
            )
            return 1

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
