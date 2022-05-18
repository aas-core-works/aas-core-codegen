"""Merge constrained primitives as property constraints."""
import collections
from typing import Tuple, Optional, List, Mapping, MutableMapping, Sequence

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import Error
from aas_core_codegen.infer_for_schema import (
    _len as infer_for_schema_len,
    _pattern as infer_for_schema_pattern,
)
from aas_core_codegen.infer_for_schema._types import (
    ConstraintsByProperty,
    LenConstraint,
    PatternConstraint,
)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _infer_len_constraints_by_constrained_primitive(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[
    Optional[MutableMapping[intermediate.ConstrainedPrimitive, LenConstraint]],
    Optional[List[Error]],
]:
    """Infer the constraints on ``len(.)`` of the constrained primitives."""

    # NOTE (mristin, 2022-02-11):
    # We do this inference in two passes. In the first pass, we only infer
    # the constraints defined for the constrained primitive and ignore the ancestors.
    # In the second pass, we stack the constraints of the ancestors as well.

    errors = []  # type: List[Error]

    first_pass: MutableMapping[
        intermediate.ConstrainedPrimitive, LenConstraint
    ] = collections.OrderedDict()

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.ConstrainedPrimitive):
            (
                len_constraint,
                len_constraint_errors,
            ) = infer_for_schema_len.infer_len_constraint_of_self(
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
        intermediate.ConstrainedPrimitive, LenConstraint
    ] = collections.OrderedDict()

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
    pattern_verifications_by_name: infer_for_schema_pattern.PatternVerificationsByName,
) -> MutableMapping[intermediate.ConstrainedPrimitive, List[PatternConstraint]]:
    """Infer the pattern constraints of the constrained strings."""

    # NOTE (mristin, 2022-02-11):
    # We do this inference in two passes. In the first pass, we only infer
    # the constraints defined for the constrained primitive and ignore the ancestors.
    # In the second pass, we stack the constraints of the ancestors as well.

    first_pass: MutableMapping[
        intermediate.ConstrainedPrimitive,
        List[PatternConstraint],
    ] = collections.OrderedDict()

    for symbol in symbol_table.symbols:
        if (
            isinstance(symbol, intermediate.ConstrainedPrimitive)
            and symbol.constrainee is intermediate.PrimitiveType.STR
        ):
            pattern_constraints = infer_for_schema_pattern.infer_patterns_on_self(
                constrained_primitive=symbol,
                pattern_verifications_by_name=pattern_verifications_by_name,
            )

            first_pass[symbol] = pattern_constraints

    second_pass: MutableMapping[
        intermediate.ConstrainedPrimitive,
        List[PatternConstraint],
    ] = collections.OrderedDict()

    for symbol in first_pass:
        # NOTE (mristin, 2022-02-11):
        # We make the copy in order to avoid bugs when we start processing
        # the inheritances.
        pattern_constraints = first_pass[symbol][:]

        for inheritance in symbol.inheritances:
            assert inheritance in first_pass, (
                f"We are processing the constrained primitive {symbol.name!r}. "
                f"However, its parent, {inheritance.name!r}, has not been processed in "
                f"the first pass. Something probably went wrong in the first pass."
            )

            inherited_pattern_constraints = second_pass.get(inheritance, None)
            assert inherited_pattern_constraints is not None, (
                f"Expected topological order. However, the symbol {symbol.name!r} "
                f"is being processed before one of its parents, {inheritance.name!r}."
            )

            pattern_constraints = inherited_pattern_constraints + pattern_constraints

        second_pass[symbol] = pattern_constraints

    return second_pass


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def infer_constraints_by_class(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[
    Optional[MutableMapping[intermediate.ClassUnion, ConstraintsByProperty]],
    Optional[List[Error]],
]:
    """Infer the constraints from the invariants and constrained primitives."""
    errors = []  # type: List[Error]

    pattern_verifications_by_name = (
        infer_for_schema_pattern.map_pattern_verifications_by_name(
            verifications=symbol_table.verification_functions
        )
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

    patterns_by_constrained_primitive = (
        _infer_pattern_constraints_by_constrained_primitive(
            symbol_table=symbol_table,
            pattern_verifications_by_name=pattern_verifications_by_name,
        )
    )

    result: MutableMapping[
        intermediate.ClassUnion, ConstraintsByProperty
    ] = collections.OrderedDict()

    for symbol in symbol_table.symbols:
        if not isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        # region Infer constraints on ``len(.)``

        len_constraints_by_property: MutableMapping[
            intermediate.Property, LenConstraint
        ] = collections.OrderedDict()

        (
            len_constraints_from_invariants,
            len_constraints_errors,
        ) = infer_for_schema_len.len_constraints_from_invariants(cls=symbol)

        if len_constraints_errors is not None:
            errors.extend(len_constraints_errors)
            continue

        assert len_constraints_from_invariants is not None

        patterns_by_property: MutableMapping[
            intermediate.Property, List[PatternConstraint]
        ] = collections.OrderedDict()

        patterns_from_invariants_by_property = (
            infer_for_schema_pattern.patterns_from_invariants(
                cls=symbol, pattern_verifications_by_name=pattern_verifications_by_name
            )
        )

        # region Merge the length constraints

        for prop in symbol.properties:
            # NOTE (mristin, 2022-03-03):
            # We need to go beneath ``Optional`` as the constraints are applied even
            # if a property is optional. In cases where cardinality is affected by
            # ``Optional``, the client code needs to cover them separately.
            type_anno = intermediate.beneath_optional(prop.type_annotation)

            len_constraint_from_type: Optional[LenConstraint] = None

            len_constraint_from_invariants = len_constraints_from_invariants.get(
                prop, None
            )

            if isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
                type_anno.symbol, intermediate.ConstrainedPrimitive
            ):
                len_constraint_from_type = len_constraints_by_constrained_primitive.get(
                    type_anno.symbol, None
                )

            # Merge the constraint from the type and from the invariants

            if (
                len_constraint_from_type is None
                and len_constraint_from_invariants is None
            ):
                pass

            elif (
                len_constraint_from_type is not None
                and len_constraint_from_invariants is None
            ):
                if (
                    len_constraint_from_type.min_value is not None
                    or len_constraint_from_type.max_value is not None
                ):
                    len_constraints_by_property[prop] = len_constraint_from_type

            elif (
                len_constraint_from_type is None
                and len_constraint_from_invariants is not None
            ):
                if (
                    len_constraint_from_invariants.min_value is not None
                    or len_constraint_from_invariants.max_value is not None
                ):
                    len_constraints_by_property[prop] = len_constraint_from_invariants

            elif (
                len_constraint_from_type is not None
                and len_constraint_from_invariants is not None
            ):
                # NOTE (mristin, 2022-03-02):
                # We have to make the bounds *stricter* since both
                # the type constraints and the invariant(s) need to be satisfied.

                min_value = infer_for_schema_len.max_with_none(
                    len_constraint_from_type.min_value,
                    len_constraint_from_invariants.min_value,
                )

                max_value = infer_for_schema_len.min_with_none(
                    len_constraint_from_type.max_value,
                    len_constraint_from_invariants.max_value,
                )

                if (
                    min_value is not None
                    and max_value is not None
                    and min_value > max_value
                ):
                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The inferred minimum and maximum value on len(.) "
                            f"is contradictory: "
                            f"minimum = {min_value}, maximum = {max_value}; "
                            f"please check the invariants and "
                            f"any involved constrained primitives",
                        )
                    )
                    continue

                if min_value is not None or max_value is not None:
                    len_constraints_by_property[prop] = LenConstraint(
                        min_value=min_value, max_value=max_value
                    )

            else:
                raise AssertionError(
                    f"Unhandled case: "
                    f"{len_constraint_from_type=}, {len_constraint_from_invariants}"
                )

        # endregion

        # region Infer constraints on string patterns

        for prop in symbol.properties:
            # NOTE (mristin, 2022-03-03):
            # We need to go beneath ``Optional`` as the constraints are applied even
            # if a property is optional. In cases where cardinality is affected by
            # ``Optional``, the client code needs to cover them separately.
            type_anno = intermediate.beneath_optional(prop.type_annotation)

            patterns_from_type: List[PatternConstraint] = []
            patterns_from_invariants = patterns_from_invariants_by_property.get(
                prop, []
            )

            if isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
                type_anno.symbol, intermediate.ConstrainedPrimitive
            ):
                patterns_from_type = patterns_by_constrained_primitive.get(
                    type_anno.symbol, []
                )

            merged = patterns_from_type + patterns_from_invariants

            if len(merged) > 0:
                patterns_by_property[prop] = merged

        # endregion

        result[symbol] = ConstraintsByProperty(
            len_constraints_by_property=len_constraints_by_property,
            patterns_by_property=patterns_by_property,
        )

    if len(errors) > 0:
        return None, errors

    return result, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def merge_constraints_with_ancestors(
    symbol_table: intermediate.SymbolTable,
    constraints_by_class: Mapping[intermediate.ClassUnion, ConstraintsByProperty],
) -> Tuple[
    Optional[MutableMapping[intermediate.ClassUnion, ConstraintsByProperty]],
    Optional[Error],
]:
    """
    Merge the constraints over all the classes with their ancestors.

    Usually, when you generate a schema, you do *not* want to inherit the constraints
    over the properties. Most schema engines will do that for you and you want to be
    as explicit as possible in the schema for readability (whereas merged constraints
    might not be as readable, since you do not explicitly see their origin).

    However, for some applications we indeed want to stack the constraints and merge
    them. For example, this is the case when we (semi-)automatically generate test
    data. In those cases, you should use this function.

    The length constraints are merged by picking the smaller interval that fits.
    Patterns are simply stacked together.
    """
    new_constraints_by_class: MutableMapping[
        intermediate.ClassUnion, ConstraintsByProperty
    ] = collections.OrderedDict()

    for symbol in symbol_table.symbols_topologically_sorted:
        if not isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        this_constraints_by_props = constraints_by_class[symbol]

        new_len_constraints_by_property: MutableMapping[
            intermediate.Property, LenConstraint
        ] = collections.OrderedDict()

        new_patterns_by_property: MutableMapping[
            intermediate.Property, Sequence[PatternConstraint]
        ] = collections.OrderedDict()

        for prop in symbol.properties:
            # region Merge len constraints

            len_constraints = []

            this_len_constraint = (
                this_constraints_by_props.len_constraints_by_property.get(prop, None)
            )
            if this_len_constraint is not None:
                len_constraints.append(this_len_constraint)

            for parent in symbol.inheritances:
                # NOTE (mristin, 2022-05-15):
                # Assume here that all the ancestors already inherited their constraints due to
                # the topological order in the iteration.
                that_constraints_by_props = new_constraints_by_class[parent]

                that_len_constraint = (
                    that_constraints_by_props.len_constraints_by_property.get(
                        prop, None
                    )
                )
                if that_len_constraint is not None:
                    len_constraints.append(that_len_constraint)

            min_value = None
            max_value = None

            for len_constraint in len_constraints:
                if min_value is None:
                    min_value = len_constraint.min_value
                else:
                    if len_constraint.min_value is not None:
                        min_value = max(len_constraint.min_value, min_value)

                if max_value is None:
                    max_value = len_constraint.max_value
                else:
                    if len_constraint.max_value is not None:
                        max_value = min(len_constraint.max_value, max_value)

            if (
                min_value is not None
                and max_value is not None
                and min_value > max_value
            ):
                return None, Error(
                    symbol.parsed.node,
                    f"We could not stack the length constraints "
                    f"on the property {prop.name} as they are contradicting: "
                    f"min_value == {min_value} and max_value == {max_value}. "
                    f"Please check the invariants and the invariants of all "
                    f"the ancestors.",
                )

            if min_value is not None or max_value is not None:
                new_len_constraints_by_property[prop] = LenConstraint(
                    min_value=min_value, max_value=max_value
                )

            # endregion

            # region Merge patterns

            # NOTE (mristin, 2022-05-15):
            # The following logic has quadratic time complexity, but it seems that
            # the runtime is currently no problem in practice.

            patterns = []  # type: List[PatternConstraint]

            this_patterns = this_constraints_by_props.patterns_by_property.get(
                prop, None
            )
            if this_patterns is not None:
                patterns.extend(this_patterns)

            for parent in symbol.inheritances:
                # NOTE (mristin, 2022-05-15):
                # Assume here that all the ancestors already inherited their constraints due to
                # the topological order in the iteration.
                that_constraints_by_props = new_constraints_by_class[parent]

                that_patterns = that_constraints_by_props.patterns_by_property.get(
                    prop, None
                )

                if that_patterns is not None:
                    patterns.extend(that_patterns)

            if len(patterns) > 0:
                new_patterns_by_property[prop] = patterns

            # endregion

        new_constraints_by_class[symbol] = ConstraintsByProperty(
            len_constraints_by_property=new_len_constraints_by_property,
            patterns_by_property=new_patterns_by_property,
        )

    return new_constraints_by_class, None
