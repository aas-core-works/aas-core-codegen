"""Generate the SHACL schema based on the meta-model."""

# TODO: review everything in this file!

from typing import MutableMapping, Any, Union, Tuple, Optional, List

from icontract import ensure

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error, assert_never


def _define_for_enumeration(
        enumeration: intermediate.Enumeration
) -> Stripped:
    """Generate the definition for an ``enumeration``."""
    raise NotImplementedError()


# TODO: fix
_BUILTIN_MAP = {
    intermediate.BuiltinAtomicType.BOOL: "boolean",
    intermediate.BuiltinAtomicType.INT: "integer",
    intermediate.BuiltinAtomicType.FLOAT: "number",
    intermediate.BuiltinAtomicType.STR: "string"
}
assert all(literal in _BUILTIN_MAP for literal in intermediate.BuiltinAtomicType)


def _generate_for_class_or_interface(
        symbol: Union[intermediate.Interface, intermediate.Class]
) -> Stripped:
    """Generate the constraints for the intermediate ``symbol``."""
    raise NotImplementedError()


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the SHACL schema based on the ``symbol_table."""
    preamble_key = specific_implementations.ImplementationKey(
        "shacl/preamble.ttl"
    )

    preamble = spec_impls.get(preamble_key, None)
    if preamble is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the SHACL preamble "
                f"is missing: {preamble_key}")]

    blocks = []  # type: List[Stripped]

    # TODO: uncomment once implemented
    # for symbol in symbol_table.symbols:
    #     block = None  # type: Optional[Stripped]
    #
    #     if isinstance(symbol, intermediate.Enumeration):
    #         block = _define_for_enumeration(enumeration=symbol)
    #     elif isinstance(symbol, (intermediate.Interface, intermediate.Class)):
    #         block = _generate_for_class_or_interface(symbol=symbol)
    #     else:
    #         assert_never(symbol)
    #
    #     assert block is not None
    #     blocks.append(block)

    return Stripped('\n\n'.join(blocks)), None
