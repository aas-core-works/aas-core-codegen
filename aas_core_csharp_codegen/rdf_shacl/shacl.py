"""Generate the SHACL schema based on the meta-model."""
import io
import textwrap
from typing import Union, Tuple, Optional, List, MutableMapping, Sequence, Mapping

from icontract import ensure, require

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_csharp_codegen.parse import (
    tree as parse_tree
)
from aas_core_csharp_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common
)
from aas_core_csharp_codegen.rdf_shacl.common import (
    INDENT as I
)


class Cardinality:
    """Represent cardinality of a property."""

    def __init__(self, min_count: Optional[int], max_count: Optional[int]) -> None:
        """Initialize with the given values."""
        self.min_count = min_count
        self.max_count = max_count


def _infer_cardinalities_by_properties_from_invariants(
        symbol: Union[intermediate.Interface, intermediate.Class]
) -> MutableMapping[intermediate.Property, Cardinality]:
    """Infer the cardinality of a property based on the ``symbol``'s invariants."""
    result = dict()  # type: MutableMapping[intermediate.Property, Cardinality]

    # Go over the original invariants which follows the structure of
    # the SHACL schema (instead of classes and interfaces)
    for invariant in symbol.parsed.invariants:
        if isinstance(invariant.body, parse_tree.Comparison):
            left = invariant.body.left
            right = invariant.body.right

            # noinspection PyUnresolvedReferences
            if (
                    isinstance(left, parse_tree.FunctionCall)
                    and left.name == 'len'
                    and len(left.args) == 1
                    and isinstance(left.args[0], parse_tree.Member)
                    and isinstance(left.args[0].instance, parse_tree.Name)
                    and left.args[0].instance.identifier == 'self'
                    and left.args[0].name in symbol.properties_by_name
                    and isinstance(right, parse_tree.Constant)
                    and isinstance(right.value, int)
            ):
                prop = symbol.properties_by_name[left.args[0].name]
                constant = right.value

                card = result.get(prop, None)
                if card is None:
                    card = Cardinality(min_count=None, max_count=None)
                    result[prop] = card

                # NOTE (mristin, 2021-11-13):
                # We simply overwrite the cardinality as we go.
                # Mind that this might lead to conflicts. For example,
                # imagine an invariant that says len(self.n) == 3 followed by
                # an invariant len(self.n) > 5. We ignore such conflicts and assume
                # that the invariants are consistent.

                if invariant.body.op == parse_tree.Comparator.LT:
                    card.max_count = constant - 1
                elif invariant.body.op == parse_tree.Comparator.LE:
                    card.max_count = constant
                elif invariant.body.op == parse_tree.Comparator.EQ:
                    card.max_count = constant
                    card.min_count = constant
                elif invariant.body.op == parse_tree.Comparator.GT:
                    card.min_count = constant + 1
                elif invariant.body.op == parse_tree.Comparator.GE:
                    card.min_count = constant
                elif invariant.body.op == parse_tree.Comparator.NE:
                    # We intentionally ignore the invariants of the form len(n) != X
                    # as there is no meaningful way to represent it simply in SHACL.
                    pass
                else:
                    assert_never(invariant.body.op)

    return result

_PATTERN_BY_FUNCTION = {
    'is_ID_short': r'^[a-zA-Z][a-zA-Z_0-9]*$'
}

def _infer_patterns_by_property_from_invariants(
        symbol: Union[intermediate.Interface, intermediate.Class]
) -> MutableMapping[intermediate.Property, str]:
    """Infer the pattern of a property based on the ``symbol``'s invariants."""
    result = dict()  # type: MutableMapping[intermediate.Property, str]

    # Go over the original invariants which follows the structure of
    # the SHACL schema (instead of classes and interfaces)
    for invariant in symbol.parsed.invariants:
        body = invariant.body
        # noinspection PyUnresolvedReferences
        if (
                isinstance(body, parse_tree.FunctionCall)
            and body.name in _PATTERN_BY_FUNCTION
            and len(body.args) == 1
            and isinstance(body.args[0], parse_tree.Member)
            and isinstance(body.args[0].instance, parse_tree.Name)
            and body.args[0].instance.identifier == 'self'
            and body.args[0].name in symbol.properties_by_name
        ):
            prop = symbol.properties_by_name[body.args[0].name]
            pattern = _PATTERN_BY_FUNCTION[body.name]

            result[prop] = pattern

    return result


@require(lambda prop, symbol: id(prop) in symbol.property_id_set)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_property_shape(
        prop: intermediate.Property,
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped,
        symbol_to_rdfs_range: MutableMapping[
            Union[intermediate.Interface, intermediate.Class],
            Stripped],
        inferred_cardinalities_by_properties: Mapping[intermediate.Property, Cardinality],
        inferred_patterns_by_property: Mapping[intermediate.Property, str]
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the shape of a property ``prop`` of the intermediate ``symbol``."""

    stmts = [
        Stripped("a sh:PropertyShape ;")
    ]  # type: List[Stripped]

    # Resolve the type annotation to the actual value, regardless if the property is
    # mandatory or optional
    type_anno = prop.type_annotation
    while isinstance(type_anno, intermediate.OptionalTypeAnnotation):
        type_anno = type_anno.value

    # region Define path and type

    prop_name = None  # type: Optional[Identifier]
    rdfs_range = None  # type: Optional[str]

    missing_implementation = False

    if isinstance(type_anno, intermediate.OurAtomicTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        rdfs_range = symbol_to_rdfs_range.get(
            type_anno.symbol,
            Stripped(f"aas:{rdf_shacl_naming.class_name(type_anno.symbol.name)}"))

    elif isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)
        rdfs_range = rdf_shacl_common.BUILTIN_MAP[type_anno.a_type]

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        prop_name = rdf_shacl_naming.property_name(prop.name)

        if isinstance(type_anno.items, intermediate.OurAtomicTypeAnnotation):
            rdfs_range = symbol_to_rdfs_range.get(
                type_anno.items.symbol,
                Stripped(
                    f"aas:{rdf_shacl_naming.class_name(type_anno.items.symbol.name)}"))

        elif isinstance(type_anno.items, intermediate.BuiltinAtomicTypeAnnotation):
            rdfs_range = rdf_shacl_common.BUILTIN_MAP[type_anno.items.a_type]

        else:
            missing_implementation = True
    else:
        missing_implementation = True

    if missing_implementation:
        return None, Error(
            prop.parsed.node,
            f"(mristin, 2021-11-12): "
            f"We did not refine the shape definition of "
            f"the non-atomic and non-sequential properties. "
            f"If you see this message, it is time to implement "
            f"this missing functionality.")

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

    card = Cardinality(min_count=None, max_count=None)

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        card.min_count = 0
    elif isinstance(prop.type_annotation, intermediate.ListTypeAnnotation):
        card.min_count = 0
    elif isinstance(
            prop.type_annotation, intermediate.AtomicTypeAnnotation):
        card.min_count = 1
        card.max_count = 1
    else:
        return None, Error(
            prop.parsed.node,
            f"(mristin, 2021-11-13): "
            f"We did not implement how to determine the cardinality based on the type "
            f"{prop.type_annotation}. If you see this message, it is time to implement "
            f"this logic."
        )

    inferred_card = inferred_cardinalities_by_properties.get(prop, None)

    if inferred_card is not None:
        if inferred_card.min_count is not None:
            card.min_count = (
                max(card.min_count, inferred_card.min_count)
                if card.min_count is not None
                else inferred_card.min_count)

        if inferred_card.max_count is not None:
            card.max_count = (
                min(card.max_count, inferred_card.max_count)
                if card.max_count is not None
                else inferred_card.max_count)

    if card.min_count is not None:
        stmts.append(Stripped(f'sh:minCount {card.min_count} ;'))

    if card.max_count is not None:
        stmts.append(Stripped(f'sh:maxCount {card.max_count} ;'))

    # endregion

    # region Define pattern

    pattern = inferred_patterns_by_property.get(prop, None)
    if pattern:
        stmts.append(Stripped(
            f'sh:pattern {rdf_shacl_common.string_literal(pattern)} ;'))

    # endregion

    writer = io.StringIO()
    writer.write("sh:property [")
    for stmt in stmts:
        writer.write("\n")
        writer.write(textwrap.indent(stmt, I))

    writer.write('\n] ;')

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
    prop_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    inferred_cardinalities_by_properties = _infer_cardinalities_by_properties_from_invariants(
        symbol=symbol)

    inferred_patterns_by_property = _infer_patterns_by_property_from_invariants(
        symbol=symbol)

    for prop in symbol.properties:
        prop_block, error = _define_property_shape(
            prop=prop,
            symbol=symbol,
            url_prefix=url_prefix,
            symbol_to_rdfs_range=symbol_to_rdfs_range,
            inferred_cardinalities_by_properties=inferred_cardinalities_by_properties,
            inferred_patterns_by_property=inferred_patterns_by_property)

        if error is not None:
            errors.append(error)
        else:
            assert prop_block is not None
            prop_blocks.append(prop_block)

    if len(errors) > 0:
        return None, Error(
            None,
            f"Failed to generate the shape definition for {symbol.name}",
            errors)

    shape_name = rdf_shacl_naming.class_name(Identifier(symbol.name + "_shape"))
    cls_name = rdf_shacl_naming.class_name(symbol.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        aas:{shape_name}  a sh:NodeShape ;
        {I}sh:targetClass aas:{cls_name} ;'''))

    subclasses = None  # type: Optional[Sequence[Identifier]]
    if isinstance(symbol, intermediate.Interface):
        subclasses = [inheritance.name for inheritance in symbol.inheritances]
    elif isinstance(symbol, intermediate.Class):
        subclasses = [interface.name for interface in symbol.interfaces]
    else:
        assert_never(symbol)

    for subclass in subclasses:
        subclass_name = rdf_shacl_naming.class_name(subclass)
        writer.write(f'\n{I}rdfs:subClassOf {subclass_name} ;')

    for block in prop_blocks:
        writer.write('\n')
        writer.write(textwrap.indent(block, I))

    writer.write('\n.')

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
        symbol_table: intermediate.SymbolTable,
        symbol_to_rdfs_range: MutableMapping[
            Union[intermediate.Interface, intermediate.Class], Stripped],
        spec_impls: specific_implementations.SpecificImplementations,
        url_prefix: Stripped
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the SHACL schema based on the ``symbol_table."""
    errors = []  # type: List[Error]

    preamble_key = specific_implementations.ImplementationKey(
        "shacl/preamble.ttl"
    )

    preamble = spec_impls.get(preamble_key, None)
    if preamble is None:
        errors.append(Error(
            None,
            f"The implementation snippet for the SHACL preamble "
            f"is missing: {preamble_key}"))

    if len(errors) > 0:
        return None, errors

    blocks = [
        preamble
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        block = None  # type: Optional[Stripped]

        if isinstance(symbol, intermediate.Enumeration):
            continue

        if isinstance(symbol, (intermediate.Interface, intermediate.Class)):
            if (
                    isinstance(symbol, intermediate.Class)
                    and symbol.is_implementation_specific
            ):
                implementation_key = specific_implementations.ImplementationKey(
                    f"shacl/{symbol.name}/shape.ttl")

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
