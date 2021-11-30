"""Infer the constraints on the length of a property value."""
from typing import Sequence, MutableMapping, Optional, Tuple, List

from aas_core_codegen.common import assert_never, Error
from icontract import require, ensure

from aas_core_codegen import intermediate
from aas_core_codegen.parse import (
    tree as parse_tree
)
from aas_core_codegen.infer_for_schema import (
    _common as infer_for_schema_common
)


class _Constraint:
    """Represent a constraint on the ``len`` of a property."""


class _MinLength(_Constraint):
    """Represent the constraint that the ``len`` is ≥ ``value``."""

    def __init__(self, value: int) -> None:
        """Initialize with the given values."""
        self.value = value


class _MaxLength(_Constraint):
    """Represent the constraint that the ``len`` is ≤ ``value``."""

    def __init__(self, value: int) -> None:
        """Initialize with the given values."""
        self.value = value


class _ExactLength(_Constraint):
    """Represent the constraint that the ``len`` is == ``value``."""

    def __init__(self, value: int) -> None:
        """Initialize with the given values."""
        self.value = value


class LenConstraint:
    """
    Represent the constraint on the ``len`` of a property.

    Both bounds are inclusive: ``min_value ≤ len ≤ max_value``.
    """

    @require(lambda min_value, max_value: 0 < min_value <= max_value)
    def __init__(self, min_value: int, max_value: int) -> None:
        """Initialize with the given values."""
        self.min_len = min_value
        self.max_value = max_value


# TODO: simplify shacl.py once the constraints are in place!

def _match_len_constraint(node: parse_tree.Node) -> Optional[_Constraint]:
    """
    Match the constraint on ``len`` of a property.

    Mind that we match the constraint even for optional properties for which
    the invariant is conditioned on the property being specified (``is not None``).
    """
    # TODO: continue here, implement, then rewrite the code below


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def infer_len_constraints(
        cls: intermediate.Class
) -> Tuple[
    Optional[MutableMapping[intermediate.Property, LenConstraint]],
    Optional[List[Error]]
]:
    """
    Infer the constraints on ``len`` for every property of the class ``cls``.

    Even if a property is optional, the constraint will still be inferred. Please be
    careful that this does not scramble your cardinality constraints (which start from
    zero for optional properties).

    The constraints are not exhaustive. We only infer constraints based on invariants
    which involve constants. It might be that the actual invariants are tighter.
    """
    constraint_map = dict()  # MutableMapping[intermediate.Property, List[_Constraint]]

    # region Infer the constraints in the loose form from all the invariants

    # NOTE (mristin, 2021-11-30):
    # We iterate only once through the invariants instead of inferring the constraints
    # for each property individually to be able to keep linear time complexity.

    for invariant in cls.parsed.invariants:
        # Abbreviate for readability
        body = invariant.body

        comparison = None  # type: Optional[parse_tree.Comparison]
        if isinstance(invariant.body, parse_tree.Comparison):
            comparison = invariant.body

        elif (
                isinstance(invariant.body, parse_tree.Implication)
                and isinstance(invariant.body.antecedent, parse_tree.IsNotNone)
                and isinstance(invariant.body.antecedent.value, parse_tree.Member)

        ):

        # TODO: match not (self.prop is not None) or Comparison
        # TODO: match self.prop is None or Comparison

        if comparison is not None:
            left = comparison.left
            right = invariant.body.right

            # noinspection PyUnresolvedReferences
            if (
                    isinstance(left, parse_tree.FunctionCall)
                    and left.name == 'len'
                    and len(left.args) == 1
                    and isinstance(left.args[0], parse_tree.Member)
                    and isinstance(left.args[0].instance, parse_tree.Name)
                    and left.args[0].instance.identifier == 'self'
                    and left.args[0].name in cls.properties_by_name
                    and isinstance(right, parse_tree.Constant)
                    and isinstance(right.value, int)
            ):
                # noinspection PyUnresolvedReferences
                prop = cls.properties_by_name[left.args[0].name]
                constant = right.value

                constraint = None  # type: Optional[_Constraint]

                if invariant.body.op == parse_tree.Comparator.LT:
                    constraint = _MaxLength(constant - 1)
                elif invariant.body.op == parse_tree.Comparator.LE:
                    constraint = _MaxLength(constant)
                elif invariant.body.op == parse_tree.Comparator.EQ:
                    constraint = _ExactLength(constant)
                elif invariant.body.op == parse_tree.Comparator.GT:
                    constraint = _MinLength(constant + 1)
                elif invariant.body.op == parse_tree.Comparator.GE:
                    constraint = _MinLength(constant)
                elif invariant.body.op == parse_tree.Comparator.NE:
                    # We intentionally ignore the invariants of the form len(n) != X
                    # as there is no meaningful way to represent it simply in a schema.
                    pass
                else:
                    assert_never(invariant.body.op)

                constraints = constraint_map.get(prop, None)
                if constraints is None:
                    constraints = []
                    constraint_map[prop] = constraints

                constraints.append(constraint)
    # endregion

    # region Compress the loose constraints

    # endregion
