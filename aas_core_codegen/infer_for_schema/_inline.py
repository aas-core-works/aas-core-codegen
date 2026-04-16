"""Merge constrained primitives as property constraints."""
import collections
import itertools
from typing import Tuple, Optional, List, Mapping, MutableMapping, Sequence, Set, Union

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import Error
from aas_core_codegen.infer_for_schema import (
    _len as infer_for_schema_len,
    _pattern as infer_for_schema_pattern,
    _set as infer_for_schema_set,
)
from aas_core_codegen.infer_for_schema._types import (
    Constraints,
    LenConstraint,
    PatternConstraint,
    SetOfPrimitivesConstraint,
    SetOfEnumerationLiteralsConstraint,
)


# TODO: than go over constrained primitives -- and use merge on constraints
# TODO: then go over all the type annotations -- stack them for class
# TODO: then handle inheritance
def _min_or_none(
        that: Optional[float],
        other: Optional[float]
) -> Optional[float]:
    """Compute the minimum or return None if both values are None."""
    if that is not None and other is not None:
        return min(that, other)

    elif that is None and other is not None:
        return other

    elif that is not None and other is None:
        return that

    elif that is None and other is None:
        return None

    else:
        raise AssertionError("Unhandled execution path")


def _max_or_none(
        that: Optional[float],
        other: Optional[float]
) -> Optional[float]:
    """Compute the maximum or return None if both values are None."""
    if that is not None and other is not None:
        return max(that, other)

    elif that is None and other is not None:
        return other

    elif that is not None and other is None:
        return that

    elif that is None and other is None:
        return None

    else:
        raise AssertionError("Unhandled execution path")


def _merge_len_constraints(
        that: Optional[LenConstraint],
        other: Optional[LenConstraint]
) -> Optional[LenConstraint]:
    if that is not None and other is not None:
        return LenConstraint(
            min_value=_max_or_none(that.min_value, other.min_value),
            max_value=_min_or_none(that.max_value, other.max_value)
        )

    elif that is not None and other is None:
        return that

    elif that is None and other is not None:
        return other

    elif that is None and other is None:
        return None

    else:
        raise AssertionError("Unhandled execution path")


def _merge_pattern_constraints(
        that: Optional[Sequence[PatternConstraint]],
        other: Optional[Sequence[PatternConstraint]]
) -> Optional[Sequence[PatternConstraint]]:
    if that is not None and other is not None:
        observed_pattern_set: Set[str] = set()

        result: List[PatternConstraint] = []

        for pattern_constraint in itertools.chain(that, other):
            if pattern_constraint.pattern not in observed_pattern_set:
                result.append(pattern_constraint)
                observed_pattern_set.add(pattern_constraint.pattern)

        return result

    elif that is not None and other is None:
        return that

    elif that is None and other is not None:
        return other

    elif that is None and other is None:
        return None

    else:
        raise AssertionError("Unhandled execution path")


def _merge_set_of_primitives_constraints(
        that: Optional[SetOfPrimitivesConstraint],
        other: Optional[SetOfPrimitivesConstraint],
) -> Optional[SetOfPrimitivesConstraint]:
    if that is not None and other is not None:
        if that.a_type != other.a_type:
            raise ValueError(
                "Constraints on sets of primitives of different primitive types "
                f"can not be merged together; that primitive type is {that.a_type}, "
                f"other primitive type is {other.a_type}."
            )

        observed_value_set: Set[Union[bool, int, float, str, bytearray]] = set()

        literals: List[intermediate.PrimitiveSetLiteral] = []

        for literal in itertools.chain(that.literals, other.literals):
            if literal.value not in observed_value_set:
                literals.append(literal)
                observed_value_set.add(literal.value)

        return SetOfPrimitivesConstraint(
            # NOTE (mristin):
            # We simply pick one of the types as we assert before that that.a_type
            # and other.a_type must be the same.
            a_type=that.a_type,
            literal=literals
        )

    elif that is not None and other is None:
        return that

    elif that is None and other is not None:
        return other

    elif that is None and other is None:
        return None

    else:
        raise AssertionError("Unhandled execution path")


def _merge_set_of_enumeration_literals_constraints(
        that: Optional[SetOfEnumerationLiteralsConstraint],
        other: Optional[SetOfEnumerationLiteralsConstraint],
) -> Optional[SetOfEnumerationLiteralsConstraint]:
    if that is not None and other is not None:
        if that.enumeration is not other.enumeration:
            raise ValueError(
                "Constraints on sets of enumeration literals of different enumerations "
                f"can not be merged together; that enumeration is {that.enumeration}, "
                f"other enumeration is {other.enumeration}."
            )

        # TODO: remove
        #     enumeration: Final[intermediate.Enumeration]
        #     literals: Final[Sequence[intermediate.EnumerationLiteral]]

        observed_literal_id_set: Set[int] = set()

        literals: List[intermediate.EnumerationLiteral] = []

        for literal in itertools.chain(that.literals, other.literals):
            if id(literal) not in observed_literal_id_set:
                literals.append(literal)
                observed_literal_id_set.add(id(literal))

        return SetOfEnumerationLiteralsConstraint(
            # NOTE (mristin):
            # We simply pick one of the enumerations as we assert before that
            # enumeration and other enumeration are one and the same.
            a_type=that.enumeration,
            literal=literals
        )

    elif that is not None and other is None:
        return that

    elif that is None and other is not None:
        return other

    elif that is None and other is None:
        return None

    else:
        raise AssertionError("Unhandled execution path")


def _merge_constraints(
        that: Optional[Constraints],
        other: Optional[Constraints]
) -> Optional[Constraints]:
    """Combine the constraints on tighter bounds."""
    if that is not None and other is not None:
        return Constraints(
            len_constraint=_merge_len_constraints(
                that.len_constraint,
                other.len_constraint
            ),
            patterns=_merge_pattern_constraints(
                that.patterns,
                other.patterns
            ),
            set_of_primitives=_merge_set_of_primitives_constraints(
                that.set_of_primitives,
                other.set_of_primitives
            ),
            set_of_enumeration_literals=_merge_set_of_enumeration_literals_constraints(
                that.set_of_enumeration_literals,
                other.set_of_enumeration_literals
            )
        )

    elif that is not None and other is None:
        return that

    elif that is None and other is not None:
        return other

    elif that is None and other is None:
        return None

    else:
        raise AssertionError("Unhandled execution path")


def _infer_constraints_of_constrained_primitive_without_inheritance(
        constrained_primitive: intermediate.ConstrainedPrimitive,
        pattern_verifications_by_name: infer_for_schema_pattern.PatternVerificationsByName,
) -> Tuple[Optional[Constraints], Optional[List[Error]]]:
    """
    Infer the constraints from the invariants on self of the constrained primitive.

    We do not go up (or down) the inheritance tree -- the constraints from the parents
    are not inherited at this step.

    If there are no constraints inferred from the constrained primitive, we return None.
    """
    errors = []  # type: List[Error]

    len_constraint: Optional[LenConstraint] = None

    if constrained_primitive.constrainee in infer_for_schema_len.LENGTHABLE_PRIMITIVES:
        (
            len_constraint,
            len_constraint_errors,
        ) = infer_for_schema_len.infer_len_constraint_of_self(
            constrained_primitive=constrained_primitive
        )

        if len_constraint_errors is not None:
            errors.extend(len_constraint_errors)
        else:
            assert len_constraint is not None

            # NOTE (mristin):
            # We do not want to keep dummy constraints.
            if len_constraint.min_value is None and len_constraint.max_value is None:
                len_constraint = None

    pattern_constraints: Optional[Sequence[PatternConstraint]] = None

    if constrained_primitive.constrainee is intermediate.PrimitiveType.STR:
        pattern_constraints = infer_for_schema_pattern.infer_patterns_on_self(
            constrained_primitive=constrained_primitive,
            pattern_verifications_by_name=pattern_verifications_by_name,
        )

        if len(pattern_constraints) == 0:
            # NOTE (mristin):
            # We do not want to keep dummy constraints.
            pattern_constraints = None

    if len(errors) > 0:
        return None, errors

    if len_constraint is None and pattern_constraints is None:
        return None, None

    return Constraints(
        len_constraint=len_constraint,
        patterns=pattern_constraints,
        # NOTE (mristin):
        # We do not match the set of primitives on the constrained primitives at the
        # moment, but this could be easily implemented.
        set_of_primitives=None,
        set_of_enumeration_literals=None,
    ), None


@ensure(lambda result: not (result[1] is not None) or len(result[1]) > 0)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _infer_constraints_by_constrained_primitive(
        symbol_table: intermediate.SymbolTable,
) -> Tuple[
    Optional[MutableMapping[intermediate.ConstrainedPrimitive, Constraints]],
    Optional[List[Error]]
]:
    """
    Infer the constraints from the constrained primitives considering the inheritance.
    
    If there are no constraints for the given constrained primitive, it is not present
    in the mapping.
    """
    errors: List[Error] = []

    mapping: MutableMapping[intermediate.ConstrainedPrimitive, Constraints] = dict()

    pattern_verifications_by_name = (
        infer_for_schema_pattern.map_pattern_verifications_by_name(
            verifications=symbol_table.verification_functions
        )
    )

    # NOTE (mristin):
    # We perform the first pass where we disregard inheritance and return if there are
    # any errors. We can then be certain that there will be no errors when we stack
    # the constraints considering the inheritance tree.

    for constrained_primitive in symbol_table.constrained_primitives:
        constraints, errors_constrained_primitive = (
            _infer_constraints_of_constrained_primitive_without_inheritance(
                constrained_primitive=constrained_primitive,
                pattern_verifications_by_name=pattern_verifications_by_name,
            )
        )

        if errors_constrained_primitive is not None:
            errors.append(
                Error(
                    constrained_primitive.parsed.node,
                    f"Failed to infer the schema constraints "
                    f"from constrained primitive {constrained_primitive.name!r}",
                    errors_constrained_primitive
                )
            )

        if constraints is not None:
            mapping[constrained_primitive] = constraints

    if len(errors) > 0:
        return None, errors

    for our_type in symbol_table.our_types_topologically_sorted:
        if not isinstance(our_type, intermediate.ConstrainedPrimitive):
            continue

        # NOTE (mristin):
        # We rename for clarity when the reader reads the previous code.
        constrained_primitive = our_type

        constraints = mapping.get(constrained_primitive, None)

        # NOTE (mristin):
        # The topological order ensures that we have processed the parents already.
        for parent in constrained_primitive.inheritances:
            constraints = _merge_constraints(constraints, mapping.get(parent, None))

        if constraints is not None:
            mapping[constrained_primitive] = constraints

    return mapping, None



# TODO: rewrite intensively!
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

    for cls in symbol_table.classes:
        # region Infer constraints on ``len(.)``

        len_constraints_by_property: MutableMapping[
            intermediate.Property, LenConstraint
        ] = collections.OrderedDict()

        (
            len_constraints_from_invariants,
            len_constraints_errors,
        ) = infer_for_schema_len.len_constraints_from_invariants(cls=cls)

        if len_constraints_errors is not None:
            errors.extend(len_constraints_errors)
            continue

        assert len_constraints_from_invariants is not None

        patterns_by_property: MutableMapping[
            intermediate.Property, List[PatternConstraint]
        ] = collections.OrderedDict()

        patterns_from_invariants_by_property = (
            infer_for_schema_pattern.patterns_from_invariants(
                cls=cls,
                pattern_verifications_by_name=pattern_verifications_by_name,
            )
        )

        # region Merge the length constraints

        for prop in cls.properties:
            # NOTE (mristin, 2022-03-03):
            # We need to go beneath ``Optional`` as the constraints are applied even
            # if a property is optional. In cases where cardinality is affected by
            # ``Optional``, the client code needs to cover them separately.
            type_anno = intermediate.beneath_optional(prop.type_annotation)

            len_constraint_from_type: Optional[LenConstraint] = None

            len_constraint_from_invariants = len_constraints_from_invariants.get(
                prop, None
            )

            if (
                    isinstance(type_anno, intermediate.OurTypeAnnotation)
                    and isinstance(type_anno.our_type,
                                   intermediate.ConstrainedPrimitive)
                    # NOTE (mristin, 2023-02-06):
                    # We infer constraints for constrained primitives only for
                    # the class that defines the property, and skip these constraints
                    # in the descendant classes. This is necessary to avoid
                    # unnecessary repetitions of constraints in the schemas.
                    #
                    # In case your schema engine *does not* support inheritance or other
                    # forms of stacking constraints over classes, see the method
                    # ``merge_constraints_with_ancestors``.
                    and prop.specified_for is cls
            ):
                len_constraint_from_type = len_constraints_by_constrained_primitive.get(
                    type_anno.our_type, None
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
                            cls.parsed.node,
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

        for prop in cls.properties:
            # NOTE (mristin, 2022-03-03):
            # We need to go beneath ``Optional`` as the constraints are applied even
            # if a property is optional. In cases where cardinality is affected by
            # ``Optional``, the client code needs to cover them separately.
            type_anno = intermediate.beneath_optional(prop.type_annotation)

            patterns_from_type: List[PatternConstraint] = []
            patterns_from_invariants = patterns_from_invariants_by_property.get(
                prop, []
            )

            if (
                    isinstance(type_anno, intermediate.OurTypeAnnotation)
                    and isinstance(type_anno.our_type,
                                   intermediate.ConstrainedPrimitive)
                    # NOTE (mristin, 2023-02-06):
                    # We infer constraints for constrained primitives only for
                    # the class that defines the property, and skip these constraints
                    # in the descendant classes. This is necessary to avoid
                    # unnecessary repetitions of constraints in the schemas.
                    #
                    # In case your schema engine *does not* support inheritance or other
                    # forms of stacking constraints over classes, see the method
                    # ``merge_constraints_with_ancestors``.
                    and prop.specified_for is cls
            ):
                patterns_from_type = patterns_by_constrained_primitive.get(
                    type_anno.our_type, []
                )

            merged = patterns_from_type + patterns_from_invariants

            if len(merged) > 0:
                patterns_by_property[prop] = merged

        # endregion

        # region Infer constraints on constant sets

        # fmt: off
        set_constraints, some_errors = (
            infer_for_schema_set.infer_set_constraints_by_property_from_invariants(
                cls=cls,
                symbol_table=symbol_table
            )
        )
        # fmt: on

        if some_errors is not None:
            errors.extend(some_errors)
            continue

        assert set_constraints is not None

        # endregion

        # fmt: off
        result[cls] = ConstraintsByProperty(
            len_constraints_by_property=len_constraints_by_property,
            patterns_by_property=patterns_by_property,
            set_of_primitives_by_property=set_constraints.set_of_primitives_by_property,
            set_of_enumeration_literals_by_property=(
                set_constraints.set_of_enumeration_literals_by_property
            )
        )
        # fmt: on

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
    over the properties. Most schema engines will do that for you, and you want to be
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

    for our_type in symbol_table.our_types_topologically_sorted:
        if not isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue

        this_constraints_by_props = constraints_by_class[our_type]

        new_len_constraints_by_property: MutableMapping[
            intermediate.Property, LenConstraint
        ] = collections.OrderedDict()

        new_patterns_by_property: MutableMapping[
            intermediate.Property, Sequence[PatternConstraint]
        ] = collections.OrderedDict()

        new_set_of_primitives_by_property: MutableMapping[
            intermediate.Property, SetOfPrimitivesConstraint
        ] = collections.OrderedDict()

        new_set_of_enum_literals_by_property: MutableMapping[
            intermediate.Property, SetOfEnumerationLiteralsConstraint
        ] = collections.OrderedDict()

        for prop in our_type.properties:
            # region Merge len constraints

            len_constraints = []

            this_len_constraint = (
                this_constraints_by_props.len_constraints_by_property.get(prop, None)
            )
            if this_len_constraint is not None:
                len_constraints.append(this_len_constraint)

            for parent in our_type.inheritances:
                # NOTE (mristin, 2022-05-15):
                # Assume here that all the ancestors already inherited their constraints
                # due to the topological order in the iteration.
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
                    our_type.parsed.node,
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

            set_of_this_patterns = (
                set()
                if this_patterns is None
                else set(this_pattern.pattern for this_pattern in this_patterns)
            )

            for parent in our_type.inheritances:
                # NOTE (mristin, 2022-05-15):
                # Assume here that all the ancestors already inherited their constraints
                # due to the topological order in the iteration.
                that_constraints_by_props = new_constraints_by_class[parent]

                that_patterns = that_constraints_by_props.patterns_by_property.get(
                    prop, None
                )

                if that_patterns is not None:
                    for that_pattern in that_patterns:
                        # NOTE (mristin, 2022-06-15):
                        # We have to make sure that we do not inherit the same pattern
                        # from the parent.
                        #
                        # This is particularly important if the inherited property is a
                        # constrained primitive. In that case, if we didn't check for
                        # the duplicates, we would inherit the same pattern multiple
                        # times as we can not distinguish whether the pattern
                        # comes from an invariant of the parent or an invariant of
                        # the constrained primitive.
                        if that_pattern.pattern not in set_of_this_patterns:
                            patterns.append(that_pattern)

            if len(patterns) > 0:
                new_patterns_by_property[prop] = patterns

            # endregion

            # region Merge sets of primitives

            sets_of_primitives = []  # type: List[SetOfPrimitivesConstraint]

            # fmt: off
            this_set_of_primitives = (
                this_constraints_by_props.set_of_primitives_by_property.get(prop, None)
            )
            # fmt: on

            if this_set_of_primitives is not None:
                sets_of_primitives.append(this_set_of_primitives)

            for parent in our_type.inheritances:
                # NOTE (mristin, 2022-07-08):
                # Assume here that all the ancestors already inherited their constraints
                # due to the topological order in the iteration.

                that_constraints_by_props = new_constraints_by_class[parent]

                # fmt: off
                that_set_of_primitives = (
                    that_constraints_by_props.set_of_primitives_by_property.get(
                        prop, None)
                )
                # fmt: on

                if that_set_of_primitives is not None:
                    sets_of_primitives.append(that_set_of_primitives)

            if len(sets_of_primitives) > 0:
                # fmt: off
                new_set_of_primitives_by_property[prop] = (
                    infer_for_schema_set.intersect_set_of_primitives_constraints(
                        constraints=sets_of_primitives)
                )
                # fmt: on

            # endregion

            # region Merge sets of enumeration literals

            sets_of_enum_literals = []  # type: List[SetOfEnumerationLiteralsConstraint]

            # fmt: off
            this_set_of_enum_literals = (
                this_constraints_by_props.set_of_enumeration_literals_by_property.get(
                    prop, None
                )
            )
            # fmt: on

            if this_set_of_enum_literals is not None:
                sets_of_enum_literals.append(this_set_of_enum_literals)

            for parent in our_type.inheritances:
                # NOTE (mristin, 2022-07-08):
                # Assume here that all the ancestors already inherited their constraints
                # due to the topological order in the iteration.

                that_constraints_by_props = new_constraints_by_class[parent]

                # fmt: off
                that_set_of_enum_literals = (
                    that_constraints_by_props
                    .set_of_enumeration_literals_by_property
                    .get(
                        prop, None
                    )
                )
                # fmt: on

                if that_set_of_enum_literals is not None:
                    sets_of_enum_literals.append(that_set_of_enum_literals)

            if len(sets_of_enum_literals) > 0:
                # fmt: off
                new_set_of_enum_literals_by_property[prop] = (
                    infer_for_schema_set
                    .intersect_set_of_enumeration_literals_constraints(
                        constraints=sets_of_enum_literals
                    )
                )
                # fmt: on

            # endregion

        new_constraints_by_class[our_type] = ConstraintsByProperty(
            len_constraints_by_property=new_len_constraints_by_property,
            patterns_by_property=new_patterns_by_property,
            set_of_primitives_by_property=new_set_of_primitives_by_property,
            set_of_enumeration_literals_by_property=new_set_of_enum_literals_by_property,
        )

    for our_type, constraints_by_property in new_constraints_by_class.items():
        for (
                prop,
                set_of_primitives,
        ) in constraints_by_property.set_of_primitives_by_property.items():
            if len(set_of_primitives.literals) == 0:
                return None, Error(
                    prop.parsed.node,
                    f"The property {prop.name!r} of our type {our_type.name!r} "
                    f"is constrained to an empty set of primitive literals",
                )

        for (
                prop,
                set_of_enum_literals,
        ) in constraints_by_property.set_of_enumeration_literals_by_property.items():
            if len(set_of_enum_literals.literals) == 0:
                return None, Error(
                    prop.parsed.node,
                    f"The property {prop.name!r} of our type {our_type.name!r} "
                    f"is constrained to an empty set of enumeration literals",
                )

    return new_constraints_by_class, None
