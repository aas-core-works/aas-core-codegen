"""Read and prepare specific implementations."""
import pathlib
import re
from typing import cast, Mapping, Optional, List, Sequence, Union

from icontract import require

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Error, Stripped, assert_never

IMPLEMENTATION_KEY_RE = re.compile('[a-zA-Z_][a-zA-Z_0-9]*(/[a-zA-Z_][a-zA-Z_0-9]*)*')


class ImplementationKey(str):
    """
    Represent a key in the map of specific implementations.

    A key follows the schema:

    * ``{symbol name}`` for the symbols with specific implementation,
    * ``{symbol name}/{method name}`` for the methods with the specific implementation,
    * ``{general snippet identifier}`` for snippets which are not tied to a symbol
    """

    @require(lambda key: IMPLEMENTATION_KEY_RE.fullmatch(key))
    def __new__(cls, key: str) -> 'ImplementationKey':
        return cast(ImplementationKey, key)


SpecificImplementations = Mapping[ImplementationKey, Stripped]


def _verify_that_available_for_symbol(
        intermediate_symbol: intermediate.Symbol,
        spec_impls: SpecificImplementations
) -> Optional[Error]:
    """Check that all the necessary implementations are provided for the symbol."""
    errors = []  # type: List[Error]

    # TODO: we need to fix this. If we have an abstract implementation-specific
    #  entity, we need to propagate the implementation to all the descendants!
    #  The current solution is really buggy and misleading.

    if (
            isinstance(intermediate_symbol, intermediate.Class)
            and intermediate_symbol.is_implementation_specific
    ):
        key = intermediate_symbol.name

        if key not in spec_impls:
            errors.append(
                Error(
                    intermediate_symbol.parsed.node,
                    f"The implementation with the key {key!r} is missing "
                    f"for the whole symbol, "
                    f"but it was declared implementation-specific"))

        for method in intermediate_symbol.methods:
            if method.is_implementation_specific:
                key = f"{intermediate_symbol.name}/{method.name}"
                if key not in spec_impls:
                    errors.append(
                        Error(
                            method.parsed.node,
                            f"The implementation with the key {key} is missing "
                            f"for the method {method.name!r}, "
                            f"but it was declared implementation-specific"))

        if intermediate_symbol.constructor.is_implementation_specific:
            key = f"{intermediate_symbol.name}/__init__"
            if key not in spec_impls:
                errors.append(
                    Error(
                        intermediate_symbol.parsed.node,
                        f"The implementation of the constructor with the key {key} "
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


def verify_that_available_for_all_symbols(
        intermediate_symbol_table: intermediate.SymbolTable,
        spec_impls: SpecificImplementations
) -> List[Error]:
    errors = []  # type: List[Error]
    for symbol in intermediate_symbol_table.symbols:
        error = _verify_that_available_for_symbol(
            intermediate_symbol=symbol, spec_impls=spec_impls)

        if error is not None:
            errors.append(error)

    return errors
