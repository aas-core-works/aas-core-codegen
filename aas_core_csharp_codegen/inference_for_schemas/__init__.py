"""
Infer constraints for schemas (JSON Schema, XSD *etc.*) based on the invariants.

Mind that many constraints *can not* be modeled by the schemas (*e.g.*, lower bound
smaller than the upper bound in a range), and are thus not inferred.
"""
from typing import Optional, List, Union, MutableMapping, Tuple

from icontract import require, ensure

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import assert_never, Error
from aas_core_csharp_codegen.parse import (
    tree as parse_tree
)


class Constraint:
    """Represent the common constraints that schemas can model."""


class MinOccurrences(Constraint):
    """Represent the expected minimum number of occurrences."""

    def __init__(self, value: int) -> None:
        """Initialize with the given values."""
        self.value = value


class MaxOccurrences(Constraint):
    """Represent the expected maximum number of occurrences."""

    def __init__(self, value: int) -> None:
        """Initialize with the given values."""
        self.value = value


class ExactOccurrences(Constraint):
    """Represent the expected exact number of occurrences."""

    def __init__(self, value: int) -> None:
        """Initialize with the given values."""
        self.value = value


class Pattern(Constraint):
    """
    Represent the expected regular expression.

    Please control yourself that the pattern matches your schema implementation in terms
    of special symbols and characters.
    """

    def __init__(self, value: str) -> None:
        """Initialize with the given values."""
        self.value = value


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def infer(
        symbol: Union[intermediate.Interface, intermediate.Class],
        symbol_table: intermediate.SymbolTable
) -> Tuple[
    Optional[MutableMapping[intermediate.Property, List[Constraint]]],
    Optional[List[Error]]
]:
    """
    Infer the constraints for each property based on the invariants.

    Errors are only returned if the inferred constraints are inconsistent.
    The invariants which we could not understand are simply ignored.
    """
    mapping = dict()  # type: MutableMapping[intermediate.Property, List[Constraint]]

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
                prop = symbol.properties_by_name.get(left.args[0].name, None)
                if prop is not None:
                    constant = right.value

                    constraint = None  # type: Optional[Constraint]

                    if invariant.body.op == parse_tree.Comparator.LT:
                        constraint = MaxOccurrences(constant - 1)
                    elif invariant.body.op == parse_tree.Comparator.LE:
                        constraint = MaxOccurrences(constant)
                    elif invariant.body.op == parse_tree.Comparator.EQ:
                        constraint = ExactOccurrences(constant)
                    elif invariant.body.op == parse_tree.Comparator.GT:
                        constraint = MinOccurrences(constant + 1)
                    elif invariant.body.op == parse_tree.Comparator.GE:
                        constraint = MinOccurrences(constant)
                    elif invariant.body.op == parse_tree.Comparator.NE:
                        # We intentionally ignore the invariants of the form len(n) != X
                        # as there is no meaningful way to represent them in schemas.
                        pass
                    else:
                        assert_never(invariant.body.op)

                    constraints = mapping.get(prop, None)
                    if constraints is None:
                        constraints = []
                        mapping[prop] = constraints

                    constraints.append(constraint)

        # TODO: match if there is a pattern

    # TODO: use allOf in JSON schema to stack constraints!

    # TODO: refactor shacl.py
