"""Provide common functions for both RDF and SHACL generators."""
from typing import MutableMapping, Union, Tuple, Optional, List

from icontract import ensure

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error

INDENT = "    "
INDENT2 = INDENT * 2
INDENT3 = INDENT * 3
INDENT4 = INDENT * 4


def string_literal(text: str) -> Stripped:
    """Generate a valid and escaped string literal based on the free-form ``text``."""
    if len(text) == 0:
        return Stripped('""')

    escaped = text.replace('"', '\\"')
    if '\n' in escaped:
        return Stripped(f'"""{escaped}"""')
    else:
        return Stripped(f'"{escaped}"')


SymbolToRdfsRange = MutableMapping[
    Union[intermediate.Interface, intermediate.Class], Stripped]


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def determine_symbol_to_rdfs_range(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[SymbolToRdfsRange], Optional[Error]]:
    """
    Iterate over all the symbols and determine their value as ``rdfs:range``.

    This also applies for ``sh:datatype`` in SHACL.
    """

    symbol_to_rdfs_range = dict()  # type: SymbolToRdfsRange
    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        if (
                isinstance(symbol, intermediate.Class)
                and symbol.is_implementation_specific
        ):
            implementation_key = specific_implementations.ImplementationKey(
                f"rdf/{symbol.name}/as_rdfs_range.ttl")
            implementation = spec_impls.get(implementation_key, None)
            if implementation is None:
                errors.append(Error(
                    symbol.parsed.node,
                    f"The implementation snippet for "
                    f"how to represent the class {symbol.parsed.name} "
                    f"as ``rdfs:range`` is missing: {implementation_key}"))
            else:
                symbol_to_rdfs_range[symbol] = implementation

    if len(errors) > 0:
        return None, Error(
            None,
            "Failed to determine the mapping symbol 🠒 ``rdfs:range`` "
            "for one or more symbols",
            errors)

    return symbol_to_rdfs_range, None


BUILTIN_MAP = {
    intermediate.BuiltinAtomicType.BOOL: "xsd:boolean",
    intermediate.BuiltinAtomicType.INT: "xsd:integer",
    intermediate.BuiltinAtomicType.FLOAT: "xsd:double",
    intermediate.BuiltinAtomicType.STR: "xsd:string",
    intermediate.BuiltinAtomicType.BYTEARRAY: "xsd:byte"
}
assert all(literal in BUILTIN_MAP for literal in intermediate.BuiltinAtomicType)
