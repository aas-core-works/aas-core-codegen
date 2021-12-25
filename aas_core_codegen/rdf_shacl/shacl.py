"""Generate the SHACL schema based on the meta-model."""
import io
import textwrap
from typing import Union, Tuple, Optional, List, MutableMapping, Sequence, Mapping

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations, infer_for_schema
from aas_core_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
)
from aas_core_codegen.rdf_shacl.common import INDENT as I


@require(lambda prop, symbol: id(prop) in symbol.property_id_set)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_property_shape(
    prop: intermediate.Property,
    symbol: Union[intermediate.Interface, intermediate.Class],
    url_prefix: Stripped,
    symbol_to_rdfs_range: MutableMapping[
        Union[intermediate.Interface, intermediate.Class], Stripped
    ],
    len_constraints_by_property: Mapping[
        intermediate.Property, infer_for_schema.LenConstraint
    ],
    pattern_constraints_by_property: Mapping[
        intermediate.Property, List[infer_for_schema.PatternConstraint]
    ],
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the shape of a property ``prop`` of the intermediate ``symbol``."""

    stmts = [Stripped("a sh:PropertyShape ;")]  # type: List[Stripped]

    # Resolve the type annotation to the actual value, regardless if the property is
    # mandatory or optional
    type_anno = rdf_shacl_common.beneath_optional_and_ref(prop.type_annotation)

    # region Define path and type

    prop_name = None  # type: Optional[Identifier]
    rdfs_range = None  # type: Optional[str]

    missing_implementation = False

    if isinstance(type_anno, intermediate.OurTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        rdfs_range = symbol_to_rdfs_range.get(
            type_anno.symbol,
            Stripped(f"aas:{rdf_shacl_naming.class_name(type_anno.symbol.name)}"),
        )

    elif isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        rdfs_range = rdf_shacl_common.PRIMITIVE_MAP[type_anno.a_type]

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)

        type_anno_items = rdf_shacl_common.beneath_optional_and_ref(type_anno.items)

        if isinstance(type_anno_items, intermediate.OurTypeAnnotation):
            rdfs_range = symbol_to_rdfs_range.get(
                type_anno_items.symbol,
                Stripped(
                    f"aas:{rdf_shacl_naming.class_name(type_anno_items.symbol.name)}"
                ),
            )

        elif isinstance(type_anno_items, intermediate.PrimitiveTypeAnnotation):
            rdfs_range = rdf_shacl_common.PRIMITIVE_MAP[type_anno_items.a_type]

        else:
            missing_implementation = True
    else:
        missing_implementation = True

    if missing_implementation:
        # fmt: off
        return None, Error(
            prop.parsed.node,
            f"(mristin, 2021-11-12): "
            f"We did not refine the shape definition of "
            f"the non-atomic and non-sequential properties. "
            f"If you see this message, it is time to implement "
            f"this missing functionality.\n"
            f"{prop=}, {type_anno=}, {symbol=}")
        # fmt: on

    assert prop_name is not None
    assert rdfs_range is not None

    cls_name = rdf_shacl_naming.class_name(symbol.name)

    stmts.append(Stripped(f"sh:path <{url_prefix}/{cls_name}/{prop_name}> ;"))

    if rdfs_range.startswith("rdf:") or rdfs_range.startswith("xsd:"):
        stmts.append(Stripped(f"sh:datatype {rdfs_range} ;"))
    elif rdfs_range.startswith("aas:"):
        stmts.append(Stripped(f"sh:class {rdfs_range} ;"))
    else:
        raise NotImplementedError(f"Unhandled namespace of the {rdfs_range=}")

    # endregion

    # region Define cardinality

    # noinspection PyUnusedLocal
    min_count = None  # type: Optional[int]
    max_count = None  # type: Optional[int]

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        min_count = 0
    elif isinstance(prop.type_annotation, intermediate.ListTypeAnnotation):
        min_count = 0
    elif isinstance(prop.type_annotation, intermediate.RefTypeAnnotation):
        min_count = 1
        max_count = 1
    elif isinstance(prop.type_annotation, intermediate.AtomicTypeAnnotation):
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

    # NOTE (mristin, 2021-12-01):
    # We model only shape of the lists since SHACL interpretation of the string
    # length would not match the cardinality.

    if isinstance(type_anno, intermediate.ListTypeAnnotation):
        len_constraint = len_constraints_by_property.get(prop, None)

        if len_constraint is not None:

            # NOTE (mristin, 2021-12-01):
            # Mind that this will relax the exactly expected length if the list is optional.
            # However, there is not clean way to model this in SHACL that I know of.

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

    if min_count is not None:
        stmts.append(Stripped(f"sh:minCount {min_count} ;"))

    if max_count is not None:
        stmts.append(Stripped(f"sh:maxCount {max_count} ;"))

    # endregion

    # region Define pattern

    pattern_constraints = pattern_constraints_by_property.get(prop, None)
    if pattern_constraints is not None and len(pattern_constraints) > 0:
        for pattern_constraint in pattern_constraints:
            pattern_literal = rdf_shacl_common.string_literal(
                pattern_constraint.pattern
            )

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
    lambda symbol:
    not isinstance(symbol, intermediate.Class)
    or not symbol.is_implementation_specific
)
# fmt: on
def _define_for_class_or_interface(
    symbol: Union[intermediate.Interface, intermediate.Class],
    symbol_to_rdfs_range: MutableMapping[
        Union[intermediate.Interface, intermediate.Class], Stripped
    ],
    url_prefix: Stripped,
    pattern_verifications_by_name: infer_for_schema.PatternVerificationsByName
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition for the intermediate ``symbol``."""
    prop_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    (
        len_constraints_by_property,
        len_constraints_errors,
    ) = infer_for_schema.infer_len_constraints_by_class_properties(symbol=symbol)

    if len_constraints_errors is not None:
        errors.extend(len_constraints_errors)

    pattern_constraints_by_property = infer_for_schema.infer_pattern_constraints(
        symbol=symbol,
        pattern_verifications_by_name=pattern_verifications_by_name
    )

    if len(errors) > 0:
        return None, Error(
            symbol.parsed.node, f"Failed to infer the constraints for {symbol.name}"
        )

    for prop in symbol.properties:
        prop_block, error = _define_property_shape(
            prop=prop,
            symbol=symbol,
            url_prefix=url_prefix,
            symbol_to_rdfs_range=symbol_to_rdfs_range,
            len_constraints_by_property=len_constraints_by_property,
            pattern_constraints_by_property=pattern_constraints_by_property,
        )

        if error is not None:
            errors.append(error)
        else:
            assert prop_block is not None
            prop_blocks.append(prop_block)

    if len(errors) > 0:
        return None, Error(
            None, f"Failed to generate the shape definition for {symbol.name}", errors
        )

    shape_name = rdf_shacl_naming.class_name(Identifier(symbol.name + "_shape"))
    cls_name = rdf_shacl_naming.class_name(symbol.name)

    writer = io.StringIO()
    writer.write(
        textwrap.dedent(
            f"""\
        aas:{shape_name}  a sh:NodeShape ;
        {I}sh:targetClass aas:{cls_name} ;"""
        )
    )

    subclasses = None  # type: Optional[Sequence[Identifier]]
    if isinstance(symbol, intermediate.Interface):
        subclasses = [inheritance.name for inheritance in symbol.inheritances]
    elif isinstance(symbol, intermediate.Class):
        subclasses = [interface.name for interface in symbol.interfaces]
    else:
        assert_never(symbol)

    for subclass in subclasses:
        subclass_name = rdf_shacl_naming.class_name(subclass)
        writer.write(f"\n{I}rdfs:subClassOf {subclass_name} ;")

    for block in prop_blocks:
        writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n.")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
    symbol_table: intermediate.SymbolTable,
    symbol_to_rdfs_range: MutableMapping[
        Union[intermediate.Interface, intermediate.Class], Stripped
    ],
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

    blocks = [preamble]  # type: List[Stripped]

    pattern_verifications_by_name = infer_for_schema.map_pattern_verifications_by_name(
        verifications=symbol_table.verification_functions
    )

    for symbol in symbol_table.symbols:
        # noinspection PyUnusedLocal
        block = None  # type: Optional[Stripped]

        if isinstance(symbol, intermediate.Enumeration):
            continue

        if isinstance(symbol, (intermediate.Interface, intermediate.Class)):
            if (
                isinstance(symbol, intermediate.Class)
                and symbol.is_implementation_specific
            ):
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
                block, error = _define_for_class_or_interface(
                    symbol=symbol,
                    symbol_to_rdfs_range=symbol_to_rdfs_range,
                    url_prefix=url_prefix,
                    pattern_verifications_by_name=pattern_verifications_by_name
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
