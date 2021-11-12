"""Generate the SHACL schema based on the meta-model."""

# TODO: review everything in this file!

from typing import MutableMapping, Any, Union, Tuple, Optional, List

from icontract import ensure

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error, assert_never




@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
        symbol_table: intermediate.SymbolTable,
        symbol_to_rdfs_range: MutableMapping[
            Union[intermediate.Interface, intermediate.Class], Stripped],
        spec_impls: specific_implementations.SpecificImplementations,
        url_prefix: Stripped
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the SHACL schema based on the ``symbol_table."""
    errors = []  # type: List[Error]

    preamble_key = specific_implementations.ImplementationKey(
        "shacl/preamble.ttl"
    )

    preamble = spec_impls.get(preamble_key, None)
    if preamble is None:
        errors.append(Error(
            None,
            f"The implementation snippet for the SHACL preamble "
            f"is missing: {preamble_key}"))

    if len(errors) > 0:
        return None, errors

    blocks = [
        preamble
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        block = None  # type: Optional[Stripped]

        if isinstance(symbol, intermediate.Enumeration):
            continue

        if isinstance(symbol, (intermediate.Interface, intermediate.Class)):
            if (
                    isinstance(symbol, intermediate.Class)
                    and symbol.is_implementation_specific
            ):
                implementation_key = specific_implementations.ImplementationKey(
                    f"shacl/{symbol.name}/shape.ttl")

                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(Error(
                        symbol.parsed.node,
                        f"The implementation snippet for "
                        f"the entity {symbol.parsed.name} "
                        f"is missing: {implementation_key}"))
                else:
                    blocks.append(implementation)

            else:
                block, error = _define_for_class_or_interface(
                    symbol=symbol,
                    symbol_to_rdfs_range=symbol_to_rdfs_range,
                    url_prefix=url_prefix)

                if error is not None:
                    errors.append(error)
                else:
                    assert block is not None
                    blocks.append(block)
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    return Stripped('\n\n'.join(blocks)), None
