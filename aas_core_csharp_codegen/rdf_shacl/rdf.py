"""Generate the RDF ontology based on the meta-model."""
import io
import textwrap
from typing import Union, Tuple, Optional, List, MutableMapping

from icontract import ensure, require

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error, assert_never, \
    plural_to_singular, Identifier
from aas_core_csharp_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II
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
def _define_for_enumeration(
        enumeration: intermediate.Enumeration,
        url_prefix: Stripped
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Define an RDF definition of an enumeration."""
    blocks = []  # type: List[Stripped]

    cls_name = rdf_shacl_naming.class_name(enumeration.name)
    cls_label = rdf_shacl_naming.class_label(enumeration.name)

    # TODO: we need to implement subclassing of Enums even though Python does not support it!
    #  🠒 we can still parse it!
    # TODO: then we need to add it here as subClassOf

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        ### {url_prefix}/{cls_name}
        aas:{cls_name} rdf:type owl:Class ;
        {I}rdfs:label {rdf_shacl_common.string_literal(cls_label)}^^xsd:string ;'''))

    errors = []  # type: List[Error]

    if enumeration.description is not None:
        comment, error = _generate_comment(enumeration.description)
        if error is not None:
            errors.append(error)
        else:
            assert comment is not None
            writer.write(
                f'{I}rdfs:comment {rdf_shacl_common.string_literal(comment)}@en ;\n')

    if len(enumeration.literals) > 0:
        writer.write(f"{I}owl:oneOf (\n")
        for literal in enumeration.literals:
            writer.write(f"{II}<{url_prefix}/{cls_name}/")


    if len(errors) > 0:
        return None, Error(
            enumeration.parsed.node,
            "Failed to generate the RDF definition",
            underlying=errors)

    return Stripped(writer.getvalue()), None

    # ### https://admin-shell.io/aas/3/0/RC01/IdentifiableElements
    # aas:IdentifiableElements rdf:type owl:Class ;
    #     rdfs:subClassOf aas:ReferableElements ;
    #     rdfs:label "Identifiable Element"^^xsd:string ;
    #     rdfs:comment "Enumeration of all identifiable elements within an asset administration shell that are not identifiable"@en ;
    #     owl:oneOf (
    #         <https://admin-shell.io/aas/3/0/RC01/IdentifiableElements/ASSET>
    #         <https://admin-shell.io/aas/3/0/RC01/IdentifiableElements/ASSET_ADMINISTRATION_SHELL>
    #         <https://admin-shell.io/aas/3/0/RC01/IdentifiableElements/CONCEPT_DESCRIPTION>
    #         <https://admin-shell.io/aas/3/0/RC01/IdentifiableElements/SUBMODEL>
    #     ) ;
    # .
    #
    # ###  https://admin-shell.io/aas/3/0/RC01/IdentifiableElements/ASSET
    # <https://admin-shell.io/aas/3/0/RC01/IdentifiableElements/ASSET> rdf:type aas:IdentifiableElements ;
    #     rdfs:label "Asset"^^xsd:string ;
    # .


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_owl_class_for_class_or_interface(
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the code to define an OWL class."""
    cls_name = rdf_shacl_naming.class_name(symbol.name)

    writer = io.StringIO()
    writer.write(f'### {url_prefix}/{cls_name}\n')
    writer.write(f'aas:{cls_name} rdf:type owl:Class ;\n')

    subclasses = []  # type: List[Identifier]
    if isinstance(symbol, intermediate.Interface):
        subclasses = [inheritance.name for inheritance in symbol.inheritances]
    elif isinstance(symbol, intermediate.Class):
        subclasses = [interface.name for interface in symbol.interfaces]
    else:
        assert_never(symbol)

    for subclass in subclasses:
        writer.write(
            f'{I}rdfs:subClassOf aas:{rdf_shacl_naming.class_name(subclass)}\n')

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


_BUILTIN_MAP = {
    intermediate.BuiltinAtomicType.BOOL: "xsd:boolean",
    intermediate.BuiltinAtomicType.INT: "xsd:integer",
    intermediate.BuiltinAtomicType.FLOAT: "xsd:double",
    intermediate.BuiltinAtomicType.STR: "xsd:string"
}
assert all(literal in _BUILTIN_MAP for literal in intermediate.BuiltinAtomicType)


@require(lambda prop, symbol: id(prop) in symbol.property_id_set)
def _define_property(
        prop: intermediate.Property,
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped,
        symbol_to_rdfs_range: MutableMapping[
            Union[intermediate.Interface, intermediate.Class],
            Stripped],
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition of a property ``prop`` of the intermediate ``symbol``."""
    # Resolve the type annotation to the actual value, regardless if the property is
    # mandatory or optional
    type_anno = prop.type_annotation
    while isinstance(type_anno, intermediate.OptionalTypeAnnotation):
        type_anno = type_anno.value

    cls_name = rdf_shacl_naming.class_name(symbol.name)
    rdfs_domain = f"aas:{cls_name}"

    prop_name = None  # type: Optional[Identifier]
    rdf_type = None  # type: Optional[str]
    rdfs_range = None  # type: Optional[str]

    missing_implementation = False

    if isinstance(type_anno, intermediate.OurAtomicTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        rdf_type = "owl:ObjectProperty"
        rdfs_range = symbol_to_rdfs_range[type_anno.symbol]

    elif isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        rdf_type = "owl:DatatypeProperty"
        rdfs_range = _BUILTIN_MAP[type_anno.a_type]

    elif isinstance(
            type_anno,
            (intermediate.ListTypeAnnotation,
             intermediate.SequenceTypeAnnotation,
             intermediate.SetTypeAnnotation)
    ):
        prop_name = rdf_shacl_naming.property_name(plural_to_singular(prop.name))

        if isinstance(type_anno.items, intermediate.OurAtomicTypeAnnotation):
            rdf_type = "owl:ObjectProperty"
            rdfs_range = symbol_to_rdfs_range[type_anno.items.symbol]

        elif isinstance(type_anno.items, intermediate.BuiltinAtomicTypeAnnotation):
            rdf_type = "owl:DatatypeProperty"
            rdfs_range = _BUILTIN_MAP[type_anno.items.a_type]

        else:
            missing_implementation = True
    else:
        missing_implementation = True

    if missing_implementation:
        return None, Error(
            prop.parsed.node,
            f"(mristin, 2021-11-12): "
            f"We did not refine the definition of the non-atomic and non-sequential "
            f"properties. If you see this message, it is time to implement "
            f"this missing functionality.")

    assert prop_name is not None
    assert rdf_type is not None
    assert rdfs_range is not None

    prop_label = rdf_shacl_naming.property_label(prop_name)

    url = f'{url_prefix}/{cls_name}/{prop_name}'
    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        ### {url}
        <{url}> rdf:type {rdf_type} ;
        {I}rdfs:label {rdf_shacl_common.string_literal(prop_label)}^^xsd:string ;
        {I}rdfs:domain {rdfs_domain} ;
        {I}rdfs:range {rdfs_range} ;'''))

    if prop.description:
        comment, error = _generate_comment(prop.description)
        if error is not None:
            return None, error

        writer.write(
            f'\n{I}rdfs:comment {rdf_shacl_common.string_literal(comment)}@en ;')

    writer.write('\n.')
    return Stripped(writer.getvalue()), None


# fmt: off
@require(
    lambda symbol:
    not isinstance(symbol, intermediate.Class)
    or not symbol.is_implementation_specific
)
# fmt: on
def _define_for_class_or_interface(
        symbol: Union[intermediate.Interface, intermediate.Class],
        symbol_to_rdfs_range: MutableMapping[
            Union[intermediate.Interface, intermediate.Class], Stripped],
        url_prefix: Stripped
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition for the intermediate ``symbol``."""
    blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    owl_class, error = _define_owl_class_for_class_or_interface(symbol=symbol,
                                                                url_prefix=url_prefix)
    if error is not None:
        errors.append(error)
    else:
        assert owl_class is not None
        blocks.append(owl_class)

    for prop in symbol.properties:
        prop_def, error = _define_property(
            prop=prop, symbol=symbol, url_prefix=url_prefix,
            symbol_to_rdfs_range=symbol_to_rdfs_range
        )
        if error is not None:
            errors.append(error)
        else:
            assert prop_def is not None
            blocks.append(prop_def)

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

    symbol_to_rdfs_range: MutableMapping[
        Union[intermediate.Interface, intermediate.Class], Stripped] = dict()

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
                    f"how to represent the entity {symbol.parsed.name} "
                    f"as ``rdfs:range`` is missing: {implementation_key}"))
            else:
                symbol_to_rdfs_range[symbol] = implementation
        else:
            symbol_to_rdfs_range[symbol] = Stripped(
                f"aas:{rdf_shacl_naming.class_name(symbol.name)}")

    for symbol in symbol_table.symbols:
        block = None  # type: Optional[Stripped]

        if isinstance(symbol, intermediate.Enumeration):
            block = _define_for_enumeration(enumeration=symbol)
        if isinstance(symbol, (intermediate.Interface, intermediate.Class)):
            if (
                    isinstance(symbol, intermediate.Class)
                    and symbol.is_implementation_specific
            ):
                implementation_key = specific_implementations.ImplementationKey(
                    f"rdf/{symbol.name}/owl_class.ttl")

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
        # else:
        #     assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    return Stripped('\n\n'.join(blocks)), None
