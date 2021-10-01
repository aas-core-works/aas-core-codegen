"""Verify the loaded specific implementations."""

# NOTE (mristin, 2021-10-01):
# We have to make this module public and separate from
# :py:mod:`aas_core_csharp_codegen.specific_implementations` to avoid
# circular dependencies in :py:mod:`aas_core_csharp_codegen.intermediate`.

from typing import Optional, List

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.specific_implementations._types import \
    SpecificImplementations

from aas_core_csharp_codegen.common import Error


def _that_available_for_symbol(
        intermediate_symbol: intermediate.Symbol,
        spec_impls: SpecificImplementations
) -> Optional[Error]:
    """Check that all the necessary implementations are provided for the symbol."""
    errors = []  # type: List[Error]

    if (
            isinstance(intermediate_symbol, intermediate.Class)
            and intermediate_symbol.implementation_key
    ):
        if intermediate_symbol.implementation_key not in spec_impls:
            errors.append(
                Error(
                    intermediate_symbol.parsed.node,
                    f"The implementation with "
                    f"the key {intermediate_symbol.implementation_key!r} "
                    f"is missing for the whole symbol, "
                    f"but it was declared implementation-specific"))

        for method in intermediate_symbol.methods:
            if method.implementation_key:
                if method.implementation_key not in spec_impls:
                    errors.append(
                        Error(
                            method.parsed.node,
                            f"The implementation with "
                            f"the key {method.implementation_key} "
                            f"is missing for the method {method.name!r}, "
                            f"but it was declared implementation-specific"))

        if intermediate_symbol.constructor.implementation_key:
            if intermediate_symbol.constructor.implementation_key not in spec_impls:
                errors.append(
                    Error(
                        intermediate_symbol.parsed.node,
                        f"The implementation of the constructor with "
                        f"the key {intermediate_symbol.constructor.implementation_key} "
                        f"is missing for the symbol {intermediate_symbol.name!r}, "
                        f"but it was declared implementation-specific"))

    else:
        pass

    if len(errors) > 0:
        return Error(
            intermediate_symbol.parsed.node,
            f"One or more specific implementations are missing "
            f"for the symbol {intermediate_symbol.name!r}",
            underlying=errors)
    return None


def that_available_for_all_symbols(
        symbol_table: intermediate.SymbolTable,
        spec_impls: SpecificImplementations
) -> List[Error]:
    errors = []  # type: List[Error]
    for symbol in symbol_table.symbols:
        error = _that_available_for_symbol(
            intermediate_symbol=symbol, spec_impls=spec_impls)

        if error is not None:
            errors.append(error)

    return errors
