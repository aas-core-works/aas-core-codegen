"""Provide common functionality across different tests."""
import os
import pathlib
from typing import List, Tuple, Optional

import asttokens
from icontract import ensure

from aas_core_codegen import parse, intermediate
from aas_core_codegen.intermediate import (
    construction as intermediate_construction,
    _hierarchy as intermediate_hierarchy
)
from aas_core_codegen.common import Error


def most_underlying_message(error: Error) -> str:
    """
    Find the message of the most underlying error.

    The errors are expected to be all chains with at most one underlying cause.
    """
    if error.underlying is None:
        return error.message

    if len(error.underlying) > 1:
        raise ValueError(
            f"Expected all errors to be in a chain, "
            f"but found an error with more than one underlying causes: {error}")

    return most_underlying_message(error.underlying[0])


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def parse_atok(
        atok: asttokens.ASTTokens
) -> Tuple[Optional[parse.SymbolTable], Optional[Error]]:
    """Parse the ``atok``, an abstract syntax tree of a meta-model."""
    import_errors = parse.check_expected_imports(atok=atok)
    if len(import_errors) > 0:
        import_errors_str = "\n".join(
            f"* {import_error}"
            for import_error in import_errors
        )

        raise AssertionError(
            f"Unexpected imports in the source code:\n{import_errors_str}")

    symbol_table, error = parse.atok_to_symbol_table(atok=atok)
    return symbol_table, error


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def parse_source(source: str) -> Tuple[Optional[parse.SymbolTable], Optional[Error]]:
    """Parse the given source text into a symbol table."""
    atok, parse_exception = parse.source_to_atok(source=source)
    if parse_exception:
        raise parse_exception

    assert atok is not None

    return parse_atok(atok=atok)


# fmt: off
@ensure(
    lambda result:
    all(
        pth.exists()
        and pth.is_file()
        and pth.name == "meta_model.py"
        for pth in result
    )
)
# fmt: on
def list_valid_meta_models_from_test_data() -> List[pathlib.Path]:
    """List the meta-models stored in the ``test_data`` project directory."""
    result = []  # type: List[pathlib.Path]

    this_dir = pathlib.Path(os.path.realpath(__file__)).parent

    meta_models_dir = this_dir.parent / "test_data/meta_models"
    if not meta_models_dir.exists():
        raise FileNotFoundError(
            f"Expected the directory containing the test meta-models "
            f"to exist: {meta_models_dir}")

    for case_dir in sorted(meta_models_dir.iterdir()):
        if not case_dir.is_dir():
            continue

        meta_model_pth = case_dir / "meta_model.py"
        if meta_model_pth.exists():
            if not meta_model_pth.is_file():
                raise RuntimeError(
                    f"Expected the meta-model to be a file, "
                    f"but it is not: {meta_model_pth}")

            result.append(meta_model_pth)

    return result


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def translate_source_to_intermediate(
        source: str
) -> Tuple[Optional[intermediate.SymbolTable], Optional[Error]]:
    atok, parse_exception = parse.source_to_atok(source=source)
    if parse_exception:
        raise parse_exception

    assert atok is not None

    parsed_symbol_table, error = parse_atok(atok=atok)
    assert error is None, f"{error=}"
    assert parsed_symbol_table is not None

    return intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        atok=atok
    )
