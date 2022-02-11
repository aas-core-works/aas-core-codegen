"""Generate the SHACL schema based on the meta-model."""
import io
import textwrap
from typing import Tuple, Optional, List, Mapping, MutableMapping

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations, infer_for_schema
from aas_core_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
)
from aas_core_codegen.rdf_shacl.common import INDENT as I


@require(lambda prop, cls: id(prop) in cls.property_id_set)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_property_shape(
    prop: intermediate.Property,
    cls: intermediate.ClassUnion,
    url_prefix: Stripped,
    class_to_rdfs_range: rdf_shacl_common.ClassToRdfsRange,
    len_constraints_by_property: Mapping[
        intermediate.Property, infer_for_schema.LenConstraint
    ],
    pattern_constraints_by_property: Mapping[
        intermediate.Property, List[infer_for_schema.PatternConstraint]
    ],
    len_constraints_by_constrained_primitive: Mapping[
        intermediate.ConstrainedPrimitive, infer_for_schema.LenConstraint
    ],
    pattern_constraints_by_constrained_primitive: Mapping[
        intermediate.ConstrainedPrimitive, List[infer_for_schema.PatternConstraint]
    ],
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the shape of a property ``prop`` of the intermediate ``symbol``."""

    stmts = [Stripped("a sh:PropertyShape ;")]  # type: List[Stripped]

    # Resolve the type annotation to the actual value, regardless if the property is
    # mandatory or optional
    type_anno = rdf_shacl_common.beneath_optional(prop.type_annotation)

    prop_name = rdf_shacl_naming.property_name(prop.name)

    rdfs_range = rdf_shacl_common.rdfs_range_for_type_annotation(
        type_annotation=type_anno, class_to_rdfs_range=class_to_rdfs_range
    )

    cls_name = rdf_shacl_naming.class_name(cls.name)

    stmts.append(Stripped(f"sh:path <{url_prefix}/{cls_name}/{prop_name}> ;"))

    if rdfs_range.startswith("rdf:") or rdfs_range.startswith("xsd:"):
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
        min_count = 0
    elif isinstance(prop.type_annotation, intermediate.ListTypeAnnotation):
        min_count = 0
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

    len_constraint = len_constraints_by_property.get(prop, None)

    if len_constraint is not None:
        if isinstance(type_anno, intermediate.ListTypeAnnotation):
            if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
                return None, Error(
                    prop.parsed.node,
                    f"(mristin, 2022-02-09): "
                    f"The property {prop.name} is optional, but the length constraint "
                    f"is given. If you see this message, it is time to implement "
                    f"this logic.",
                )

            if len_constraint.min_value is not None:
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
            and isinstance(type_anno.symbol, intermediate.ConstrainedPrimitive)
            and (
                type_anno.symbol.constrainee is intermediate.PrimitiveType.STR
                or type_anno.symbol.constrainee is intermediate.PrimitiveType.BYTEARRAY
            )
        ):
            min_length = len_constraint.min_value
            max_length = len_constraint.max_value
        else:
            return None, Error(
                prop.parsed.node,
                f"(mristin, 2022-02-09): "
                f"We did not implement how to specify the length constraint on the type "
                f"{type_anno}. If you see this message, it is time to implement "
                f"this logic.",
            )

    # NOTE (mristin, 2022-02-11):
    # We in-line here the constrained primitives as we do not want to introduce
    # a custom entity in the ontology.
    if (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and isinstance(type_anno.symbol, intermediate.ConstrainedPrimitive)
        and (
            type_anno.symbol.constrainee is intermediate.PrimitiveType.STR
            or type_anno.symbol.constrainee is intermediate.PrimitiveType.BYTEARRAY
        )
    ):
        len_constraint = len_constraints_by_constrained_primitive[type_anno.symbol]

        if len_constraint.min_value is not None:
            min_length = (
                max(min_length, len_constraint.min_value)
                if min_length is not None
                else len_constraint.min_value
            )

        if len_constraint.max_value is not None:
            max_length = (
                min(max_length, len_constraint.max_value)
                if max_length is not None
                else len_constraint.max_value
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

    pattern_constraints = pattern_constraints_by_property.get(prop, [])

    # NOTE (mristin, 2022-02-11):
    # We in-line here the constrained primitives as we do not want to introduce
    # a custom entity in the ontology.
    if (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and isinstance(type_anno.symbol, intermediate.ConstrainedPrimitive)
        and (type_anno.symbol.constrainee is intermediate.PrimitiveType.STR)
    ):
        pattern_constraints.extend(
            pattern_constraints_by_constrained_primitive.get(type_anno.symbol, [])
        )

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
    class_to_rdfs_range: rdf_shacl_common.ClassToRdfsRange,
    url_prefix: Stripped,
    pattern_verifications_by_name: infer_for_schema.PatternVerificationsByName,
    len_constraints_by_constrained_primitive: Mapping[
        intermediate.ConstrainedPrimitive, infer_for_schema.LenConstraint
    ],
    pattern_constraints_by_constrained_primitive: Mapping[
        intermediate.ConstrainedPrimitive, List[infer_for_schema.PatternConstraint]
    ],
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition for the class ``cls``."""
    prop_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    (
        len_constraints_by_property,
        len_constraints_errors,
    ) = infer_for_schema.infer_len_constraints_by_class_properties(cls=cls)

    if len_constraints_errors is not None:
        errors.extend(len_constraints_errors)

    pattern_constraints_by_property = (
        infer_for_schema.infer_patterns_by_class_properties(
            cls=cls, pattern_verifications_by_name=pattern_verifications_by_name
        )
    )

    if len(errors) > 0:
        return None, Error(
            cls.parsed.node, f"Failed to infer the constraints for {cls.name}"
        )

    assert len_constraints_by_property is not None

    for prop in cls.properties:
        prop_block, error = _define_property_shape(
            prop=prop,
            cls=cls,
            url_prefix=url_prefix,
            class_to_rdfs_range=class_to_rdfs_range,
            len_constraints_by_property=len_constraints_by_property,
            pattern_constraints_by_property=pattern_constraints_by_property,
            len_constraints_by_constrained_primitive=len_constraints_by_constrained_primitive,
            pattern_constraints_by_constrained_primitive=pattern_constraints_by_constrained_primitive,
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
        textwrap.dedent(
            f"""\
        aas:{shape_name}  a sh:NodeShape ;
        {I}sh:targetClass aas:{cls_name} ;"""
        )
    )

    for inheritance in cls.inheritances:
        subclass_name = rdf_shacl_naming.class_name(inheritance.name)
        writer.write(f"\n{I}rdfs:subClassOf {subclass_name} ;")

    for block in prop_blocks:
        writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n.")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _infer_len_constraints_by_constrained_primitive(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[
    Optional[
        MutableMapping[
            intermediate.ConstrainedPrimitive, infer_for_schema.LenConstraint
        ]
    ],
    Optional[List[Error]],
]:
    """Infer the constraints on ``len(.)`` of the constrained primitives."""

    # NOTE (mristin, 2022-02-11):
    # We do this inference in two passes. In the first pass, we only infer
    # the constraints defined for the constrained primitive and ignore the ancestors.
    # In the second pass, we stack the constraints of the ancestors as well.

    errors = []  # type: List[Error]

    first_pass: MutableMapping[
        intermediate.ConstrainedPrimitive, infer_for_schema.LenConstraint
    ] = dict()

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.ConstrainedPrimitive):
            (
                len_constraint,
                len_constraint_errors,
            ) = infer_for_schema.infer_len_constraint_of_self(
                constrained_primitive=symbol
            )

            if len_constraint_errors is not None:
                errors.extend(len_constraint_errors)
            else:
                assert len_constraint is not None

                first_pass[symbol] = len_constraint

    if len(errors) > 0:
        return None, errors

    second_pass: MutableMapping[
        intermediate.ConstrainedPrimitive, infer_for_schema.LenConstraint
    ] = dict()

    for symbol in symbol_table.symbols_topologically_sorted:
        if isinstance(symbol, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-02-11):
            # We make the copy in order to avoid bugs when we start processing
            # the inheritances.
            len_constraint = first_pass[symbol].copy()

            for inheritance in symbol.inheritances:
                inherited_len_constraint = second_pass.get(inheritance, None)
                assert (
                    inherited_len_constraint is not None
                ), "Expected topological order"

                if inherited_len_constraint.min_value is not None:
                    len_constraint.min_value = (
                        max(
                            len_constraint.min_value, inherited_len_constraint.min_value
                        )
                        if len_constraint.min_value is not None
                        else inherited_len_constraint.min_value
                    )

                if inherited_len_constraint.max_value is not None:
                    len_constraint.max_value = (
                        min(
                            len_constraint.max_value, inherited_len_constraint.max_value
                        )
                        if len_constraint.max_value is not None
                        else inherited_len_constraint.max_value
                    )

            second_pass[symbol] = len_constraint

    assert len(errors) == 0
    return second_pass, None


def _infer_pattern_constraints_by_constrained_primitive(
    symbol_table: intermediate.SymbolTable,
    pattern_verifications_by_name: infer_for_schema.PatternVerificationsByName,
) -> MutableMapping[
    intermediate.ConstrainedPrimitive, List[infer_for_schema.PatternConstraint]
]:
    """Infer the pattern constraints of the constrained strings."""

    # NOTE (mristin, 2022-02-11):
    # We do this inference in two passes. In the first pass, we only infer
    # the constraints defined for the constrained primitive and ignore the ancestors.
    # In the second pass, we stack the constraints of the ancestors as well.

    first_pass: MutableMapping[
        intermediate.ConstrainedPrimitive, List[infer_for_schema.PatternConstraint]
    ] = dict()

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.ConstrainedPrimitive):
            pattern_constraints = infer_for_schema.infer_patterns_on_self(
                constrained_primitive=symbol,
                pattern_verifications_by_name=pattern_verifications_by_name,
            )

            first_pass[symbol] = pattern_constraints

    second_pass: MutableMapping[
        intermediate.ConstrainedPrimitive, List[infer_for_schema.PatternConstraint]
    ] = dict()

    for symbol in symbol_table.symbols_topologically_sorted:
        if isinstance(symbol, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-02-11):
            # We make the copy in order to avoid bugs when we start processing
            # the inheritances.
            pattern_constraints = first_pass[symbol][:]

            for inheritance in symbol.inheritances:
                inherited_pattern_constraints = second_pass.get(inheritance, None)
                assert (
                    inherited_pattern_constraints is not None
                ), "Expected topological order"

                pattern_constraints = (
                    inherited_pattern_constraints + pattern_constraints
                )

            second_pass[symbol] = pattern_constraints

    return second_pass


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
    symbol_table: intermediate.SymbolTable,
    class_to_rdfs_range: rdf_shacl_common.ClassToRdfsRange,
    spec_impls: specific_implementations.SpecificImplementations,
    url_prefix: Stripped,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the SHACL schema based on the ``symbol_table."""
    errors = []  # type: List[Error]

    preamble_key = specific_implementations.ImplementationKey("shacl/preamble.ttl")

    preamble = spec_impls.get(preamble_key, None)
    if preamble is None:
        errors.append(
            Error(
                None,
                f"The implementation snippet for the SHACL preamble "
                f"is missing: {preamble_key}",
            )
        )

    if len(errors) > 0:
        return None, errors

    assert preamble is not None
    blocks = [preamble]  # type: List[Stripped]

    pattern_verifications_by_name = infer_for_schema.map_pattern_verifications_by_name(
        verifications=symbol_table.verification_functions
    )

    (
        len_constraints_by_constrained_primitive,
        some_errors,
    ) = _infer_len_constraints_by_constrained_primitive(symbol_table=symbol_table)
    if some_errors is not None:
        errors.extend(some_errors)

    if len(errors) > 0:
        return None, errors

    assert len_constraints_by_constrained_primitive is not None

    pattern_constraints_by_constrained_primitive = (
        _infer_pattern_constraints_by_constrained_primitive(
            symbol_table=symbol_table,
            pattern_verifications_by_name=pattern_verifications_by_name,
        )
    )

    for symbol in symbol_table.symbols:
        # noinspection PyUnusedLocal
        block = None  # type: Optional[Stripped]

        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-02-11):
            # We in-line the constraints from the constrained primitives directly in the
            # properties. We do not want to introduce separate entities for them as that
            # would unnecessarily pollute the ontology.
            continue

        elif isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if symbol.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"shacl/{symbol.name}/shape.ttl"
                )

                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The implementation snippet for "
                            f"the class {symbol.parsed.name} "
                            f"is missing: {implementation_key}",
                        )
                    )
                else:
                    blocks.append(implementation)

            else:
                block, error = _define_for_class(
                    cls=symbol,
                    class_to_rdfs_range=class_to_rdfs_range,
                    url_prefix=url_prefix,
                    pattern_verifications_by_name=pattern_verifications_by_name,
                    len_constraints_by_constrained_primitive=(
                        len_constraints_by_constrained_primitive
                    ),
                    pattern_constraints_by_constrained_primitive=(
                        pattern_constraints_by_constrained_primitive
                    ),
                )

                if error is not None:
                    errors.append(error)
                else:
                    assert block is not None
                    blocks.append(block)
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    return Stripped("\n\n".join(blocks)), None
