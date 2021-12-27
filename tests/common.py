"""Provide common functionality across different tests."""
import os
import pathlib
from typing import List, Tuple, Optional

import asttokens
from icontract import ensure

from aas_core_codegen import parse, intermediate
from aas_core_codegen.intermediate import (
    construction as intermediate_construction,
    _hierarchy as intermediate_hierarchy,
)
from aas_core_codegen.common import Error


def most_underlying_messages(error: Error) -> str:
    """Find the "leaf" errors and render them as a new-line separated list."""
    if error.underlying is None:
        return error.message

    most_underlying_errors = []  # type: List[Error]

    stack = error.underlying  # type: List[Error]

    while len(stack) > 0:
        top_error = stack.pop()

        if top_error.underlying is not None:
            stack.extend(top_error.underlying)

        if top_error.underlying is None or len(top_error.underlying) == 0:
            most_underlying_errors.append(top_error)

    return "\n".join(
        most_underlying_error.message
        for most_underlying_error in most_underlying_errors
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def parse_atok(
    atok: asttokens.ASTTokens,
) -> Tuple[Optional[parse.SymbolTable], Optional[Error]]:
    """Parse the ``atok``, an abstract syntax tree of a meta-model."""
    import_errors = parse.check_expected_imports(atok=atok)
    if len(import_errors) > 0:
        import_errors_str = "\n".join(
            f"* {import_error}" for import_error in import_errors
        )

        raise AssertionError(
            f"Unexpected imports in the source code:\n{import_errors_str}"
        )

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


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def translate_source_to_intermediate(
    source: str,
) -> Tuple[Optional[intermediate.SymbolTable], Optional[Error]]:
    atok, parse_exception = parse.source_to_atok(source=source)
    if parse_exception:
        raise parse_exception

    assert atok is not None

    parsed_symbol_table, error = parse_atok(atok=atok)
    assert error is None, f"{most_underlying_messages(error)}"
    assert parsed_symbol_table is not None

    return intermediate.translate(parsed_symbol_table=parsed_symbol_table, atok=atok)
