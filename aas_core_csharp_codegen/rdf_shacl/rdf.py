"""Generate the RDF ontology based on the meta-model."""
import enum
import io
from typing import Union, Tuple, Optional, List

import docutils
import docutils.nodes
from icontract import ensure

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_csharp_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
    _description as rdf_shacl_description
)
from aas_core_csharp_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II
)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_comment(
        description: intermediate.Description
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """
    Generate the comment text based on the description.

    The description might come either from an interface or a class, or from
    a property.
    """
    if len(description.document.children) == 0:
        return Stripped(""), None

    renderer = rdf_shacl_description.Renderer()
    tokens, error = [renderer.transform(child) for child in description.document.children]




def _define_owl_class(
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped
) -> Stripped:
    """Generate the code to define an OWL class."""
    cls_name = rdf_shacl_naming.class_name(symbol.name)

    writer = io.StringIO()
    writer.write(f'### {url_prefix}/{cls_name}\n')
    writer.write(f'aas:{cls_name} rdf:type owl:Class ;\n')

    if symbol.description is not None:
        comment = _generate_comment(symbol.description)

        writer.write(
            f'{I}rdfs:comment {rdf_shacl_common.string_literal(comment)}@en ;\n')

    cls_label = rdf_shacl_naming.class_label(symbol.name)
    writer.write(
        f'{I}rdfs:label {rdf_shacl_common.string_literal(cls_label)}^^xsd:string ;\n')

    writer.write('.')
    return Stripped(writer.getvalue())


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
