"""Generate the SHACL schema based on the meta-model."""
import io
import textwrap
from typing import Tuple, Optional, List

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations, infer_for_schema
from aas_core_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_codegen.infer_for_schema import PatternConstraint
from aas_core_codegen.jsonschema import main as jsonschema_main
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
    pattern_constraint: PatternConstraint,
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """
    Generate the shape of a property ``prop`` of the intermediate ``cls``.

    Return `""` if there are no constraints imposed on this property.
    """

    len_constraint = constraints_by_property.len_constraints_by_property.get(prop, None)

    # NOTE (mristin, 2023-02-08):
    # This check might come as a bit off. In SHACL, to the best of our understanding —
    # we are no experts — we have to define the cardinality as 0..1 or 1..1 if there are
    # no constraints inherited from the parent class.
    #
    # If the parent class already specified the property and its shape, we skip any
    # further constraints in the descendant classes.
    if (
        len_constraint is None
        and pattern_constraint is None
        and prop.specified_for is not cls
    ):
        return Stripped(""), None

    stmts = [Stripped("a sh:PropertyShape ;")]  # type: List[Stripped]

    # Resolve the type annotation to the actual value, regardless if the property is
    # mandatory or optional
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    prop_name = rdf_shacl_naming.property_name(prop.name)

    rdfs_range = rdf_shacl_common.rdfs_range_for_type_annotation(
        type_annotation=type_anno, our_type_to_rdfs_range=our_type_to_rdfs_range
    )

    # NOTE (mhrimaz):
    # For Subclasses of Abstract Lang String, we don't need the concert class name in the
    # property path as discussed in aas-core-codegen/issues/519
    abstract_lang_string_cls = symbol_table.find_our_type(Identifier("Abstract_lang_string"))
    if cls.is_subclass_of(abstract_lang_string_cls):
        cls_name = rdf_shacl_naming.class_name(abstract_lang_string_cls.name)
    else:
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

        elif isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
            type_anno.our_type, intermediate.Class
        ):
            return None, Error(
                prop.parsed.node,
                f"(mristin, 2023-02-08): "
                f"A length constraint has been inferred for the property {prop.name!r} "
                f"in the class {cls.name!r} whose type is "
                f"a class, namely {prop.type_annotation}. "
                f"We do not know how to impose the length constraints on "
                f"a property of type *class* in SHACL at this moment. "
                f"If this is not a bug in your meta-model, please contact "
                f"the developers to see how to implement this feature.",
            )

        else:
            return None, Error(
                prop.parsed.node,
                f"(mristin, 2022-02-09): "
                f"We did not know how the length constraint "
                f"for property {prop.name!r} in the class {cls.name!r} "
                f"of the type {type_anno} should be implemented. "
                f"If you see this message, please contact the developers "
                f"to see how to implement this feature.",
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

    if pattern_constraint:
        # NOTE (mristin):
        # We need to render the regular expression so that the pattern appears in
        # the canonical form. The original pattern in the specification might be written
        # in Python dialect, which does not translate directly to many Regex Engines.
        #
        # For example, repetition bounds can be given with 0 omitted (*e.g.*, ``{,4}``),
        # while SHACL and Java need an explicit zero (``{0, 4}``). Our standard renderer
        # puts an explicit zero.
        #
        # In addition, we render the pattern exactly as we do for JSON Schema since most
        # SHACL validators in the wild run regex engines which understand the patterns
        # for JSON Schema and work in UTF-16.
        rendered_pattern = jsonschema_main.fix_pattern_for_utf16(
            pattern_constraint.pattern
        )

        pattern_literal = rdf_shacl_common.string_literal(rendered_pattern)

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
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition for the class ``cls``."""
    prop_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    for prop in cls.properties:
        pattern_constraints = constraints_by_property.patterns_by_property.get(prop, [None,])
        for pattern_constraint in pattern_constraints:
            # NOTE (mhrimaz):
            # In SHACL, a PropertyShape cannot have multiple sh:pattern
            # this is not valid according to shacl-shacl rules
            # https://github.com/w3c/data-shapes/blob/gh-pages/shacl/shacl-shacl.ttl
            # and the behaviour of validator engine is not predictable. So we need to
            # create multiple sh:property
            prop_block, error = _define_property_shape(
                prop=prop,
                cls=cls,
                xml_namespace=xml_namespace,
                our_type_to_rdfs_range=our_type_to_rdfs_range,
                constraints_by_property=constraints_by_property,
                pattern_constraint=pattern_constraint,
                symbol_table=symbol_table
            )

            if error is not None:
                errors.append(error)
            else:
                assert prop_block is not None
                if prop_block != "":
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

        writer.write(f"\n{I}sh:node aas:{subclass_shape_name} ;")

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
{III}?this <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type .
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

    lang_string_cls, lang_string_error = rdf_shacl_common.get_lang_string_as_expected(
        symbol_table=symbol_table
    )
    if lang_string_error is not None:
        errors.append(lang_string_error)

    if len(errors) > 0:
        return None, errors

    assert constraints_by_class is not None

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

        block: Optional[Stripped]

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
                    symbol_table=symbol_table
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
