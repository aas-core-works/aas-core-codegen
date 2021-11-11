"""Generate the RDF ontology based on the meta-model."""
import io
from typing import MutableMapping, Any, Union, Tuple, Optional, List

from icontract import ensure

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error, assert_never, Identifier


def _define_for_enumeration(
        enumeration: intermediate.Enumeration
) -> Stripped:
    """Generate the definition for an ``enumeration``."""
    raise NotImplementedError()

def _rdf_class(identifier: Identifier) -> Stripped:
    """
    Produce the RDF class name from the intermediate class ``identifier``.

    >>> _rdf_class(Identifier("test"))
    'Test'

    >>> _rdf_class(Identifier("test_me"))
    'TestMe'
    """
    # TODO: continue here, implement

def _define_owl_class(
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped
) -> Stripped:
    """Generate the code to define an OWL class."""
    writer = io.StringIO()
    writer.write(f'### {url_prefix}/')


def _define_for_class_or_interface(
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped
) -> Stripped:
    """Generate the definition for the intermediate ``symbol``."""
    blocks = [
        _define_owl_class(symbol=symbol, url_prefix=url_prefix)
    ]  # type: List[Stripped]

    return Stripped('\n\n'.join(blocks))


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the JSON schema based on the ``symbol_table."""
    errors = []  # type: List[Error]

    preamble_key = specific_implementations.ImplementationKey(
        "rdf/preamble.ttl"
    )
    preamble = spec_impls.get(preamble_key, None)
    if preamble is None:
        errors.append(Error(
            None,
            f"The implementation snippet for the RDF preamble "
            f"is missing: {preamble_key}"))

    url_prefix_key = specific_implementations.ImplementationKey(
        "rdf/url_prefix.txt"
    )
    url_prefix = spec_impls.get(url_prefix_key, None)
    if url_prefix is None:
        errors.append(Error(
            None,
            f"The implementation snippet for the URL prefix of the ontology "
            f"is missing: {url_prefix_key}"))

    if len(errors) > 0:
        return None, errors

    blocks = [
        preamble
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        block = None  # type: Optional[Stripped]

        if isinstance(symbol, intermediate.Enumeration):
            block = _define_for_enumeration(enumeration=symbol)
        elif isinstance(symbol, (intermediate.Interface, intermediate.Class)):
            block = _define_for_class_or_interface(symbol=symbol)
        else:
            assert_never(symbol)

        assert block is not None
        blocks.append(block)

    return Stripped('\n\n'.join(blocks)), None
