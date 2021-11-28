"""Generate the RDF ontology based on the meta-model."""
import io
import textwrap
from typing import Union, Tuple, Optional, List, MutableMapping

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations
from aas_core_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
    _description as rdf_shacl_description
)
from aas_core_codegen.rdf_shacl.common import (
    INDENT as I,
    INDENT2 as II
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

    tokens = rdf_shacl_description.without_redundant_breaks(tokens=tokens)

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

    result = ''.join(parts)

    return result, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_for_enumeration(
        enumeration: intermediate.Enumeration,
        url_prefix: Stripped
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Define an RDF definition of an enumeration."""
    cls_name = rdf_shacl_naming.class_name(enumeration.name)
    cls_label = rdf_shacl_naming.class_label(enumeration.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        ### {url_prefix}/{cls_name}
        aas:{cls_name} rdf:type owl:Class ;'''))

    if len(enumeration.is_superset_of) > 0:
        for subset_enum in enumeration.is_superset_of:
            subset_enum_name = rdf_shacl_naming.class_name(subset_enum.name)
            writer.write(f'\nrdfs:subClassOf aas:{subset_enum_name} ;')

    writer.write(
        f'\n{I}rdfs:label {rdf_shacl_common.string_literal(cls_label)}^^xsd:string ;')

    errors = []  # type: List[Error]

    if enumeration.description is not None:
        comment, error = _generate_comment(enumeration.description)
        if error is not None:
            errors.append(error)
        else:
            assert comment is not None
            writer.write(
                f'\n{I}rdfs:comment {rdf_shacl_common.string_literal(comment)}@en ;')

    if len(enumeration.literals) > 0:
        writer.write(f"\n{I}owl:oneOf (\n")
        for literal in enumeration.literals:
            literal_name = rdf_shacl_naming.enumeration_literal(literal.name)
            writer.write(f"{II}<{url_prefix}/{cls_name}/{literal_name}>\n")

        writer.write(f"{I}) ;")

    writer.write("\n.")

    if len(enumeration.literals) > 0:
        for literal in enumeration.literals:
            literal_name = rdf_shacl_naming.enumeration_literal(literal.name)
            literal_label = rdf_shacl_naming.enumeration_literal_label(literal.name)

            writer.write('\n\n')
            writer.write(textwrap.dedent(f'''\
                ### {url_prefix}/{cls_name}/{literal_name}
                <{url_prefix}/{cls_name}/{literal_name}> rdf:type aas:{cls_name} ;
                {I}rdfs:label {rdf_shacl_common.string_literal(literal_label)}^^xsd:string ;'''))

            if literal.description is not None:
                comment, error = _generate_comment(literal.description)
                if error is not None:
                    errors.append(error)
                else:
                    assert comment is not None
                    writer.write(
                        f'\n{I}rdfs:comment '
                        f'{rdf_shacl_common.string_literal(comment)}@en ;')

            writer.write('\n.')

    if len(errors) > 0:
        return None, Error(
            enumeration.parsed.node,
            "Failed to generate the RDF definition",
            underlying=errors)

    return Stripped(writer.getvalue()), None


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


@require(lambda prop, symbol: id(prop) in symbol.property_id_set)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_property(
        prop: intermediate.Property,
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped,
        symbol_to_rdfs_range: MutableMapping[
            Union[intermediate.Interface, intermediate.Class],
            Stripped],
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition of a property ``prop`` of the intermediate ``symbol``."""
    type_anno = rdf_shacl_common.beneath_optional_and_ref(prop.type_annotation)

    cls_name = rdf_shacl_naming.class_name(symbol.name)
    rdfs_domain = f"aas:{cls_name}"

    prop_name = None  # type: Optional[Identifier]
    prop_label = None  # type: Optional[Stripped]
    rdf_type = None  # type: Optional[str]
    rdfs_range = None  # type: Optional[str]

    missing_implementation = False

    if isinstance(type_anno, intermediate.OurAtomicTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        prop_label = rdf_shacl_naming.property_label(prop.name)
        rdf_type = "owl:ObjectProperty"
        rdfs_range = symbol_to_rdfs_range.get(
            type_anno.symbol,
            Stripped(f"aas:{rdf_shacl_naming.class_name(type_anno.symbol.name)}"))

    elif isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        prop_label = rdf_shacl_naming.property_label(prop.name)
        rdf_type = "owl:DatatypeProperty"
        rdfs_range = rdf_shacl_common.BUILTIN_MAP[type_anno.a_type]

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        prop_label = rdf_shacl_naming.property_label(prop.name)

        type_anno_items = rdf_shacl_common.beneath_optional_and_ref(type_anno.items)

        if isinstance(type_anno_items, intermediate.OurAtomicTypeAnnotation):
            rdf_type = "owl:ObjectProperty"
            rdfs_range = symbol_to_rdfs_range.get(
                type_anno_items.symbol,
                Stripped(
                    f"aas:{rdf_shacl_naming.class_name(type_anno_items.symbol.name)}"))

        elif isinstance(type_anno_items, intermediate.BuiltinAtomicTypeAnnotation):
            rdf_type = "owl:DatatypeProperty"
            rdfs_range = rdf_shacl_common.BUILTIN_MAP[type_anno_items.a_type]

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
            f"this missing functionality.\n"
            f"{prop=}, {type_anno=}, {symbol=}")

    assert prop_name is not None
    assert prop_label is not None
    assert rdf_type is not None
    assert rdfs_range is not None

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

    owl_class, error = _define_owl_class_for_class_or_interface(
        symbol=symbol, url_prefix=url_prefix)
    if error is not None:
        errors.append(error)
    else:
        assert owl_class is not None
        blocks.append(owl_class)

    for prop in symbol.properties:
        if prop.implemented_for is not symbol:
            continue

        prop_def, error = _define_property(
            prop=prop, symbol=symbol, url_prefix=url_prefix,
            symbol_to_rdfs_range=symbol_to_rdfs_range
        )
        if error is not None:
            errors.append(error)
        else:
            assert prop_def is not None
            blocks.append(prop_def)

    if len(errors) > 0:
        return None, Error(
            None,
            f"Failed to generate the definition for {symbol.name}",
            errors)

    return Stripped('\n\n'.join(blocks)), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
        symbol_table: intermediate.SymbolTable,
        symbol_to_rdfs_range: rdf_shacl_common.SymbolToRdfsRange,
        spec_impls: specific_implementations.SpecificImplementations,
        url_prefix: Stripped
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

    if len(errors) > 0:
        return None, errors

    blocks = [
        preamble
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            block, error = _define_for_enumeration(
                enumeration=symbol, url_prefix=url_prefix)

            if error is not None:
                errors.append(error)
            else:
                assert block is not None
                blocks.append(block)

        elif isinstance(symbol, (intermediate.Interface, intermediate.Class)):
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
                        f"the class {symbol.parsed.name} "
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
