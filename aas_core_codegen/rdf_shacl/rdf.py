"""Generate the RDF ontology based on the meta-model."""
import io
from typing import Tuple, Optional, List

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations
from aas_core_codegen.common import Stripped, Error, assert_never
from aas_core_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
    _description as rdf_shacl_description,
)
from aas_core_codegen.rdf_shacl.common import INDENT as I, INDENT2 as II


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_summary(
    description: intermediate.DescriptionUnion,
) -> Tuple[Optional[str], Optional[Error]]:
    """Generate the comment text based on the summary in the description."""
    renderer = rdf_shacl_description.Renderer()
    tokens, errors = renderer.transform(description.summary)

    if errors is not None:
        return None, Error(
            description.parsed.node,
            "Failed to generate the description comment",
            [Error(description.parsed.node, message) for message in errors],
        )

    assert tokens is not None

    tokens = rdf_shacl_description.without_redundant_breaks(tokens=tokens)

    parts = []  # type: List[str]
    for token in tokens:
        if isinstance(token, rdf_shacl_description.TokenText):
            parts.append(token.content)
        elif isinstance(token, rdf_shacl_description.TokenLineBreak):
            parts.append("\n")
        elif isinstance(token, rdf_shacl_description.TokenParagraphBreak):
            parts.append("\n\n")
        else:
            assert_never(token)

    result = "".join(parts)

    return result, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_for_enumeration(
    enumeration: intermediate.Enumeration, xml_namespace: Stripped
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Define an RDF definition of an enumeration."""
    cls_name = rdf_shacl_naming.class_name(enumeration.name)
    cls_label = rdf_shacl_naming.class_label(enumeration.name)

    writer = io.StringIO()
    writer.write(
        f"""\
###  {xml_namespace}/{cls_name}
aas:{cls_name} rdf:type owl:Class ;"""
    )

    writer.write(
        f"\n{I}rdfs:label {rdf_shacl_common.string_literal(cls_label)}^^xs:string ;"
    )

    errors = []  # type: List[Error]

    if enumeration.description is not None:
        summary, error = _generate_summary(enumeration.description)
        if error is not None:
            errors.append(error)
        else:
            assert summary is not None
            writer.write(
                f"\n{I}rdfs:comment {rdf_shacl_common.string_literal(summary)}@en ;"
            )

    if len(enumeration.literals) > 0:
        writer.write(f"\n{I}owl:oneOf (\n")

        # NOTE (mristin, 2022-04-20):
        # We sort by the literal names so that the URLs are sorted in the resulting
        # schema.
        for literal_name in sorted(
            rdf_shacl_naming.enumeration_literal(literal.name)
            for literal in enumeration.literals
        ):
            writer.write(f"{II}<{xml_namespace}/{cls_name}/{literal_name}>\n")

        writer.write(f"{I}) ;")

    writer.write("\n.")

    if len(enumeration.literals) > 0:
        # NOTE (mristin, 2022-04-20):
        # We sort by the literal names so that the URLs are sorted in the resulting
        # schema.
        for literal_name, literal in sorted(
            (rdf_shacl_naming.enumeration_literal(literal.name), literal)
            for literal in enumeration.literals
        ):
            literal_label = rdf_shacl_naming.enumeration_literal_label(literal.name)

            writer.write("\n\n")
            writer.write(
                f"""\
###  {xml_namespace}/{cls_name}/{literal_name}
<{xml_namespace}/{cls_name}/{literal_name}> rdf:type aas:{cls_name} ;
{I}rdfs:label {rdf_shacl_common.string_literal(literal_label)}^^xs:string ;"""
            )

            if literal.description is not None:
                summary, error = _generate_summary(literal.description)
                if error is not None:
                    errors.append(error)
                else:
                    assert summary is not None
                    writer.write(
                        f"\n{I}rdfs:comment "
                        f"{rdf_shacl_common.string_literal(summary)}@en ;"
                    )

            writer.write("\n.")

    if len(errors) > 0:
        return None, Error(
            enumeration.parsed.node,
            "Failed to generate the RDF definition",
            underlying=errors,
        )

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_owl_class_for_class(
    cls: intermediate.ClassUnion, xml_namespace: Stripped
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the code to define an OWL class."""
    cls_name = rdf_shacl_naming.class_name(cls.name)

    writer = io.StringIO()
    writer.write(f"###  {xml_namespace}/{cls_name}\n")
    writer.write(f"aas:{cls_name} rdf:type owl:Class ;\n")

    for inheritance in cls.inheritances:
        writer.write(
            f"{I}rdfs:subClassOf "
            f"aas:{rdf_shacl_naming.class_name(inheritance.name)} ;\n"
        )

    cls_label = rdf_shacl_naming.class_label(cls.name)
    writer.write(
        f"{I}rdfs:label {rdf_shacl_common.string_literal(cls_label)}^^xs:string ;\n"
    )

    if cls.description is not None:
        summary, error = _generate_summary(cls.description)
        if error is not None:
            return None, error

        assert summary is not None
        writer.write(
            f"{I}rdfs:comment {rdf_shacl_common.string_literal(summary)}@en ;\n"
        )

    writer.write(".")
    return Stripped(writer.getvalue()), None


@require(lambda prop, cls: id(prop) in cls.property_id_set)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_property(
    prop: intermediate.Property,
    cls: intermediate.ClassUnion,
    xml_namespace: Stripped,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition of a property ``prop`` of the intermediate ``cls``."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    cls_name = rdf_shacl_naming.class_name(cls.name)
    rdfs_domain = f"aas:{cls_name}"

    rdf_type = None  # type: Optional[str]

    missing_implementation = False

    if isinstance(type_anno, intermediate.OurTypeAnnotation):
        if isinstance(
            type_anno.our_type,
            (
                intermediate.Enumeration,
                intermediate.AbstractClass,
                intermediate.ConcreteClass,
            ),
        ):
            rdf_type = "owl:ObjectProperty"
        elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
            rdf_type = "owl:DatatypeProperty"
        else:
            assert_never(type_anno.our_type)

    elif isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        rdf_type = "owl:DatatypeProperty"

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        type_anno_items = intermediate.beneath_optional(type_anno.items)

        if isinstance(type_anno_items, intermediate.OurTypeAnnotation):
            rdf_type = "owl:ObjectProperty"

        elif isinstance(type_anno_items, intermediate.PrimitiveTypeAnnotation):
            rdf_type = "owl:DatatypeProperty"

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
            f"{prop=}, {type_anno=}, {cls=}",
        )

    assert rdf_type is not None

    prop_name = rdf_shacl_naming.property_name(prop.name)
    prop_label = Stripped(f"has {rdf_shacl_naming.property_label(prop.name)}")
    rdfs_range = rdf_shacl_common.rdfs_range_for_type_annotation(
        type_annotation=type_anno, our_type_to_rdfs_range=our_type_to_rdfs_range
    )

    url = f"{xml_namespace}/{cls_name}/{prop_name}"
    writer = io.StringIO()
    writer.write(
        f"""\
###  {url}
<{url}> rdf:type {rdf_type} ;
{I}rdfs:label {rdf_shacl_common.string_literal(prop_label)}^^xs:string ;
{I}rdfs:domain {rdfs_domain} ;
{I}rdfs:range {rdfs_range} ;"""
    )

    if prop.description:
        summary, error = _generate_summary(prop.description)
        if error is not None:
            return None, error

        assert summary is not None

        writer.write(
            f"\n{I}rdfs:comment {rdf_shacl_common.string_literal(summary)}@en ;"
        )

    writer.write("\n.")
    return Stripped(writer.getvalue()), None


# fmt: off
@require(
    lambda cls:
    not isinstance(cls, intermediate.Class)
    or not cls.is_implementation_specific
)
# fmt: on
def _define_for_class(
    cls: intermediate.ClassUnion,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
    xml_namespace: Stripped,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition for the intermediate ``cls``."""
    blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    owl_class, error = _define_owl_class_for_class(cls=cls, xml_namespace=xml_namespace)
    if error is not None:
        errors.append(error)
    else:
        assert owl_class is not None
        blocks.append(owl_class)

    # NOTE (mristin, 2022-04-20):
    # We sort by the property names so that the URLs appear sorted in the resulting
    # schema.
    for _, prop in sorted(
        (rdf_shacl_naming.property_name(prop.name), prop) for prop in cls.properties
    ):
        if prop.specified_for is not cls or prop.strengthening_of is not None:
            continue

        prop_def, error = _define_property(
            prop=prop,
            cls=cls,
            xml_namespace=xml_namespace,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
        )
        if error is not None:
            errors.append(error)
        else:
            assert prop_def is not None
            blocks.append(prop_def)

    if len(errors) > 0:
        return None, Error(
            None, f"Failed to generate the definition for {cls.name}", errors
        )

    return Stripped("\n\n".join(blocks)), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
    symbol_table: intermediate.SymbolTable,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the RDF ontology based on the ``symbol_table."""
    errors = []  # type: List[Error]

    xml_namespace = symbol_table.meta_model.xml_namespace

    version_literal = rdf_shacl_common.string_literal(
        symbol_table.meta_model.book_version
    )

    ontology_comment_literal = rdf_shacl_common.string_literal(
        f"This ontology represents the data model for the Asset Administration Shell "
        f"according to the specification 'Details of the Asset Administration Shell - "
        f"Part 1 - Version {symbol_table.meta_model.book_version}'."
    )

    preamble = Stripped(
        f"""\
@prefix aas: <{xml_namespace}/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xs: <http://www.w3.org/2001/XMLSchema#> .
@base <{xml_namespace}/> .

<{xml_namespace}/> rdf:type owl:Ontology ;
    owl:versionInfo {version_literal} ;
    rdfs:comment {ontology_comment_literal}@en ;
    rdfs:isDefinedBy <{xml_namespace}/> ;
."""
    )

    blocks = [preamble]  # type: List[Stripped]

    lang_string_cls, lang_string_error = rdf_shacl_common.get_lang_string_as_expected(
        symbol_table=symbol_table
    )
    if lang_string_error is not None:
        errors.append(lang_string_error)

    if len(errors) > 0:
        return None, errors

    for our_type in sorted(
        symbol_table.our_types,
        key=lambda another_our_type: rdf_shacl_naming.class_name(another_our_type.name),
    ):
        if our_type is lang_string_cls:
            # NOTE (mristin, 2022-09-01):
            # Please see
            # :py:const`aas_core_codegen.rdf_shacl.common._EXPLANATION_ABOUT_WHY_WE_EXPECT_LANG_STRING`
            # on why we hard-wire ``Lang_string`` here.
            continue

        if isinstance(our_type, intermediate.Enumeration):
            block, error = _define_for_enumeration(
                enumeration=our_type, xml_namespace=xml_namespace
            )

            if error is not None:
                errors.append(error)
            else:
                assert block is not None
                blocks.append(block)

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-02-11):
            # We have to in-line the constraints of the constrained primitives directly
            # in SHACL as we do not want to introduce new entities into the ontology.
            pass

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if our_type.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"rdf/{our_type.name}/owl_class.ttl"
                )

                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            our_type.parsed.node,
                            f"The implementation snippet for "
                            f"the class {our_type.parsed.name} "
                            f"is missing: {implementation_key}",
                        )
                    )
                else:
                    blocks.append(implementation)

            else:
                block, error = _define_for_class(
                    cls=our_type,
                    our_type_to_rdfs_range=our_type_to_rdfs_range,
                    xml_namespace=xml_namespace,
                )

                if error is not None:
                    errors.append(error)
                else:
                    assert block is not None
                    blocks.append(block)
        else:
            assert_never(our_type)

    if len(errors) > 0:
        return None, errors

    return Stripped("\n\n".join(blocks)), None
