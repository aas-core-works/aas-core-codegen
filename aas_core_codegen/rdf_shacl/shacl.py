"""Generate the SHACL schema based on the meta-model."""
import io
import textwrap
from typing import Tuple, Optional, List

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations, infer_for_schema
from aas_core_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
)
from aas_core_codegen.rdf_shacl.common import INDENT as I, INDENT2 as II, INDENT3 as III


@require(lambda prop, cls: id(prop) in cls.property_id_set)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_property_shape(
    prop: intermediate.Property,
    cls: intermediate.ClassUnion,
    xml_namespace: Stripped,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the shape of a property ``prop`` of the intermediate ``cls``."""

    stmts = [Stripped("a sh:PropertyShape ;")]  # type: List[Stripped]

    # Resolve the type annotation to the actual value, regardless if the property is
    # mandatory or optional
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    prop_name = rdf_shacl_naming.property_name(prop.name)

    rdfs_range = rdf_shacl_common.rdfs_range_for_type_annotation(
        type_annotation=type_anno, our_type_to_rdfs_range=our_type_to_rdfs_range
    )

    cls_name = rdf_shacl_naming.class_name(cls.name)

    stmts.append(Stripped(f"sh:path <{xml_namespace}/{cls_name}/{prop_name}> ;"))

    if rdfs_range.startswith("rdf:") or rdfs_range.startswith("xs:"):
        stmts.append(Stripped(f"sh:datatype {rdfs_range} ;"))
    elif rdfs_range.startswith("aas:"):
        stmts.append(Stripped(f"sh:class {rdfs_range} ;"))
    else:
        raise NotImplementedError(f"Unhandled namespace of the {rdfs_range=}")

    # region Define cardinality

    # noinspection PyUnusedLocal
    min_count = None  # type: Optional[int]
    max_count = None  # type: Optional[int]

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        if isinstance(type_anno, intermediate.ListTypeAnnotation):
            min_count = 0
            max_count = None

        elif isinstance(
            type_anno,
            (intermediate.OurTypeAnnotation, intermediate.PrimitiveTypeAnnotation),
        ):
            min_count = 0
            max_count = 1

        else:
            assert_never(type_anno)

    elif isinstance(prop.type_annotation, intermediate.ListTypeAnnotation):
        min_count = 0
        max_count = None

    elif isinstance(
        prop.type_annotation,
        (intermediate.OurTypeAnnotation, intermediate.PrimitiveTypeAnnotation),
    ):
        min_count = 1
        max_count = 1

    else:
        return None, Error(
            prop.parsed.node,
            f"(mristin, 2021-11-13): "
            f"We did not implement how to determine the cardinality based on the type "
            f"{prop.type_annotation}. If you see this message, it is time to implement "
            f"this logic.",
        )

    min_length = None  # type: Optional[int]
    max_length = None  # type: Optional[int]

    len_constraint = constraints_by_property.len_constraints_by_property.get(prop, None)

    if len_constraint is not None:
        if isinstance(type_anno, intermediate.ListTypeAnnotation):
            if len_constraint.min_value is not None:
                if len_constraint.min_value > 1 and isinstance(
                    prop.type_annotation, intermediate.OptionalTypeAnnotation
                ):
                    return None, Error(
                        prop.parsed.node,
                        f"(mristin, 2022-02-09): "
                        f"The property {prop.name} is optional, but the minCount "
                        f"is larger than 1. If you see this message, it is time to "
                        f"consider how to implement this logic; please contact "
                        f"the developers.",
                    )

                # NOTE (mristin, 2022-08-19):
                # SHACL does not distinguish between optional and mandatory properties
                # (*i.e.*, nullable and non-nullable properties). Hence, we simply make
                # the optional properties as minCount 0 even though we inferred that
                # the minimum length is 1 in case that the property is null.
                if len_constraint.min_value == 1 and isinstance(
                    prop.type_annotation, intermediate.OptionalTypeAnnotation
                ):
                    min_count = 0

                else:
                    min_count = (
                        max(min_count, len_constraint.min_value)
                        if min_count is not None
                        else len_constraint.min_value
                    )

            if len_constraint.max_value is not None:
                max_count = (
                    min(max_count, len_constraint.max_value)
                    if max_count is not None
                    else len_constraint.max_value
                )
        elif (
            isinstance(type_anno, intermediate.PrimitiveTypeAnnotation)
            and type_anno.a_type is intermediate.PrimitiveType.STR
        ):
            min_length = len_constraint.min_value
            max_length = len_constraint.max_value

        elif (
            isinstance(type_anno, intermediate.OurTypeAnnotation)
            and isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive)
            and (
                type_anno.our_type.constrainee is intermediate.PrimitiveType.STR
                or type_anno.our_type.constrainee
                is intermediate.PrimitiveType.BYTEARRAY
            )
        ):
            min_length = len_constraint.min_value
            max_length = len_constraint.max_value
        else:
            return None, Error(
                prop.parsed.node,
                f"(mristin, 2022-02-09): "
                f"We did not implement how to specify the length constraint "
                f"on the type {type_anno}. If you see this message, it is time "
                f"to implement this logic.",
            )

    if min_count is not None:
        stmts.append(Stripped(f"sh:minCount {min_count} ;"))

    if max_count is not None:
        stmts.append(Stripped(f"sh:maxCount {max_count} ;"))

    if min_length is not None:
        stmts.append(Stripped(f"sh:minLength {min_length} ;"))

    if max_length is not None:
        stmts.append(Stripped(f"sh:maxLength {max_length} ;"))

    # endregion

    # region Define patterns

    pattern_constraints = constraints_by_property.patterns_by_property.get(prop, [])

    for pattern_constraint in pattern_constraints:
        pattern_literal = rdf_shacl_common.string_literal(pattern_constraint.pattern)

        stmts.append(Stripped(f"sh:pattern {pattern_literal} ;"))

    # endregion

    writer = io.StringIO()
    writer.write("sh:property [")
    for stmt in stmts:
        writer.write("\n")
        writer.write(textwrap.indent(stmt, I))

    writer.write("\n] ;")

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
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition for the class ``cls``."""
    prop_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    for prop in cls.properties:
        if prop.specified_for is not cls:
            continue

        prop_block, error = _define_property_shape(
            prop=prop,
            cls=cls,
            xml_namespace=xml_namespace,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
            constraints_by_property=constraints_by_property,
        )

        if error is not None:
            errors.append(error)
        else:
            assert prop_block is not None
            prop_blocks.append(prop_block)

    if len(errors) > 0:
        return None, Error(
            None, f"Failed to generate the shape definition for {cls.name}", errors
        )

    shape_name = rdf_shacl_naming.class_name(Identifier(cls.name + "_shape"))
    cls_name = rdf_shacl_naming.class_name(cls.name)

    writer = io.StringIO()
    writer.write(
        f"""\
aas:{shape_name} a sh:NodeShape ;
{I}sh:targetClass aas:{cls_name} ;"""
    )

    for inheritance in cls.inheritances:
        subclass_shape_name = rdf_shacl_naming.class_name(
            Identifier(f"{inheritance.name}_shape")
        )

        writer.write(f"\n{I}rdfs:subClassOf aas:{subclass_shape_name} ;")

    if isinstance(cls, intermediate.AbstractClass):
        writer.write("\n")
        # pylint: disable=line-too-long
        writer.write(
            textwrap.indent(
                f'''\
sh:sparql [
{I}a sh:SPARQLConstraint ;
{I}sh:message "({shape_name}): An aas:{cls_name} is an abstract class. Please use one of the subclasses for the generation of instances."@en ;
{I}sh:prefixes aas: ;
{I}sh:select """
{II}SELECT ?this ?type
{II}WHERE {{
{III}?this rdf:type ?type .
{III}FILTER (?type = aas:{cls_name})
{II}}}
{I}""" ;
] ;''',
                I,
            )
        )
        # pylint: enable=line-too-long

    for block in prop_blocks:
        writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n.")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
    symbol_table: intermediate.SymbolTable,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the SHACL schema based on the ``symbol_table."""
    errors = []  # type: List[Error]

    xml_namespace = symbol_table.meta_model.xml_namespace

    preamble = Stripped(
        f"""\
@prefix aas: <{xml_namespace}/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xs: <http://www.w3.org/2001/XMLSchema#> .

# Metadata
<{xml_namespace}/> a owl:Ontology ;
    owl:imports <http://datashapes.org/dash> ;
    owl:imports sh: ;
    sh:declare [
        a sh:PrefixDeclaration ;
        sh:namespace "{xml_namespace}/"^^xs:anyURI ;
        sh:prefix "aas"^^xs:string ;
    ] ;
."""
    )

    blocks = [preamble]  # type: List[Stripped]

    constraints_by_class, some_errors = infer_for_schema.infer_constraints_by_class(
        symbol_table=symbol_table
    )

    if some_errors is not None:
        errors.extend(some_errors)

    if len(errors) > 0:
        return None, errors

    assert constraints_by_class is not None

    for our_type in sorted(
        symbol_table.our_types,
        key=lambda another_our_type: rdf_shacl_naming.class_name(another_our_type.name),
    ):
        if our_type.name == "Lang_string":
            # NOTE (mristin, 2022-09-01):
            # We hard-wire the langString's to rdf:langString. Admittedly, this is
            # hacky. We could have made the class ``Lang_string``
            # implementation-specific and defined its ``rdfs:range`` manually as
            # a snippet.
            #
            # However, we decided against that as such a design would force us to
            # define langString for every language and schema which do not natively
            # support it, write custom data generation methods *etc.* Given that
            # RDF+SHACL codegen is one out of many code generators we leave the
            # other code generators and test data generators as simple as possible,
            # and make this code generator a bit hacky in return.
            continue

        if our_type.name == "Value_data_type":
            # NOTE (mristin, 2022-09-01):
            # We hard-wire the ``Value_data_type`` to xs:anySimpleType. Similar to
            # ``Lang_string``, this hard-wiring is hacky. We could have made
            # the class ``Value_data_type`` implementation-specific and defined its
            # ``rdfs:range`` manually as
            # a snippet.
            #
            # However, we decided against that. This would be a major hurdle for
            # other code and test data generators (which can treat ``Value_data_type``
            # simply as string). Therefore, we make the RDF+SHACL schema generator
            # a bit more hacky instead of complicating the other generators.
            #
            # If in the future, for whatever reason, the semantic of ``Value_data_type``
            # changes (or the type is renamed), be careful to maintain backwards
            # compatibility here! You probably want to distinguish different versions
            # of the meta-model and act accordingly. At that point, it might also make
            # sense to refactor this schema generator to a separate repository, and
            # fix it to a particular range of meta-model versions.
            continue

        # noinspection PyUnusedLocal
        block = None  # type: Optional[Stripped]

        if isinstance(our_type, intermediate.Enumeration):
            continue

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-02-11):
            # We in-line the constraints from the constrained primitives directly in the
            # properties. We do not want to introduce separate entities for them as that
            # would unnecessarily pollute the ontology.
            continue

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if our_type.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"shacl/{our_type.name}/shape.ttl"
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
                    constraints_by_property=constraints_by_class[our_type],
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
