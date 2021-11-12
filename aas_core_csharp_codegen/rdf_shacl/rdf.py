"""Generate the RDF ontology based on the meta-model."""
import io
from typing import Union, Tuple, Optional, List

from icontract import ensure

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error, assert_never
from aas_core_csharp_codegen.csharp.common import (
    INDENT as I
)
from aas_core_csharp_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
    _description as rdf_shacl_description
)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_comment(
        description: intermediate.Description
) -> Tuple[Optional[str], Optional[Error]]:
    """
    Generate the comment text based on the description.

    The description might come either from an interface or a class, or from
    a property.
    """
    renderer = rdf_shacl_description.Renderer()
    tokens, error = renderer.transform(description.document)

    if error:
        return None, Error(description.node, error)

    assert tokens is not None

    parts = []  # type: List[str]
    for token in tokens:
        if isinstance(token, rdf_shacl_description.TokenText):
            parts.append(token.content)
        elif isinstance(token, rdf_shacl_description.TokenLineBreak):
            parts.append('\n')
        elif isinstance(token, rdf_shacl_description.TokenParagraphBreak):
            parts.append('\n\n')
        else:
            assert_never(token)

    return ''.join(parts), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_owl_class(
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the code to define an OWL class."""
    cls_name = rdf_shacl_naming.class_name(symbol.name)

    writer = io.StringIO()
    writer.write(f'### {url_prefix}/{cls_name}\n')
    writer.write(f'aas:{cls_name} rdf:type owl:Class ;\n')

    if symbol.description is not None:
        comment, error = _generate_comment(symbol.description)
        if error is not None:
            return None, error

        assert comment is not None
        writer.write(
            f'{I}rdfs:comment {rdf_shacl_common.string_literal(comment)}@en ;\n')

    cls_label = rdf_shacl_naming.class_label(symbol.name)
    writer.write(
        f'{I}rdfs:label {rdf_shacl_common.string_literal(cls_label)}^^xsd:string ;\n')

    writer.write('.')
    return Stripped(writer.getvalue()), None


def _define_for_class_or_interface(
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition for the intermediate ``symbol``."""
    owl_class, error = _define_owl_class(symbol=symbol, url_prefix=url_prefix)
    if error is not None:
        return None, error

    assert owl_class is not None

    blocks = [
        owl_class
    ]  # type: List[Stripped]


    # TODO: if property references a mandatory or optional entity:
    # ###  https://admin-shell.io/aas/3/0/RC01/AccessControl/accessPermissionRule
    # <https://admin-shell.io/aas/3/0/RC01/AccessControl/accessPermissionRule> rdf:type owl:ObjectProperty ;
    #     rdfs:comment "Access permission rules of the AAS describing the rights assigned to (already authenticated) subjects to access elements of the AAS."@en ;
    #     rdfs:label "has access permission rule"^^xsd:string ;
    #     rdfs:domain aas:AccessControl ;
    #     rdfs:range aas:AccessPermissionRule ;

    # TODO: if property references a string:
    # ###  https://admin-shell.io/aas/3/0/RC01/AdministrativeInformation/version
    # <https://admin-shell.io/aas/3/0/RC01/AdministrativeInformation/version> rdf:type owl:DatatypeProperty ;
    #     rdfs:subPropertyOf dcterms:hasVersion ;
    #     rdfs:domain aas:AdministrativeInformation ;
    #     rdfs:range xsd:string ;
    #     rdfs:comment "Version of the element."@en ;
    #     rdfs:label "has version"^^xsd:string ;
    # .

    return Stripped('\n\n'.join(blocks)), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the RDF ontology based on the ``symbol_table."""
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
        "url_prefix.txt"
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

        # TODO: uncomment once implemented
        # if isinstance(symbol, intermediate.Enumeration):
        #     block = _define_for_enumeration(enumeration=symbol)
        if isinstance(symbol, (intermediate.Interface, intermediate.Class)):
            block, error = _define_for_class_or_interface(
                symbol=symbol, url_prefix=url_prefix)

            if error is not None:
                errors.append(error)
            else:
                assert block is not None
                blocks.append(block)
        # else:
        #     assert_never(symbol)


    return Stripped('\n\n'.join(blocks)), None
