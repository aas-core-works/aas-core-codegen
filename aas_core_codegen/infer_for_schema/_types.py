"""Provide data structures for the constraint inferences."""
import copy
from typing import Mapping, Sequence, Optional, Final, TypeAlias

from icontract import require

from aas_core_codegen import intermediate


class LenConstraint:
    """
    Represent the inferred constraint on the ``len`` of something.

    Both bounds are inclusive: ``min_value ≤ len ≤ max_value``.
    """

    min_value: Final[Optional[int]]
    max_value: Final[Optional[int]]

    # fmt: off
    @require(
        lambda min_value, max_value:
        not (min_value is not None and max_value is not None)
        or 0 < min_value <= max_value
    )
    # fmt: on
    def __init__(self, min_value: Optional[int], max_value: Optional[int]) -> None:
        """Initialize with the given values."""
        self.min_value = min_value
        self.max_value = max_value

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"min_value={self.min_value!r}, max_value={self.max_value!r})"
        )

    def equals(self, other: Optional["LenConstraint"]) -> bool:
        """Return true if the other constraint equals semantically ours."""
        if other is None:
            return False

        return self.min_value == other.min_value and self.max_value == other.max_value


class PatternConstraint:
    """Constrain a string to comply to a regular expression."""

    pattern: Final[str]

    def __init__(self, pattern: str) -> None:
        """Initialize with the given values."""
        self.pattern = pattern

    def __repr__(self) -> str:
        """Represent the constraint with the pattern."""
        return (
            f"<{self.__class__.__name__} at 0x{id(self):x} "
            f"with pattern={self.pattern!r}>"
        )

    def equals(self, other: Optional["PatternConstraint"]) -> bool:
        """Return true if the other constraint equals semantically ours."""
        if other is None:
            return False

        return self.pattern == other.pattern


class SetOfPrimitivesConstraint:
    """Constrain a primitive value to be a member of a pre-defined set of values."""

    a_type: Final[intermediate.PrimitiveType]
    literals: Final[Sequence[intermediate.PrimitiveSetLiteral]]

    # fmt: off
    @require(
        lambda a_type, literals:
        all(
            literal.a_type is a_type
            for literal in literals
        )
    )
    # fmt: on
    def __init__(
            self,
            a_type: intermediate.PrimitiveType,
            literals: Sequence[intermediate.PrimitiveSetLiteral],
    ) -> None:
        """Initialize with the given values."""
        self.a_type = a_type
        self.literals = literals

    def __repr__(self) -> str:
        """Represent the constraint with the pattern."""
        return f"<{self.__class__.__name__} at 0x{id(self):x}>"

    def equals(self, other: Optional["SetOfPrimitivesConstraint"]) -> bool:
        """Return true if the other constraint equals semantically ours."""
        if other is None:
            return False

        return (
                self.a_type == other.a_type
                and len(self.literals) == len(other.literals)
                and all(
            id(that_literal) == id(other_literal)
            for that_literal, other_literal in zip(self.literals, other.literals)
        )
        )


class SetOfEnumerationLiteralsConstraint:
    """Constrain a value to be a member of a pre-defined set of values."""

    enumeration: Final[intermediate.Enumeration]
    literals: Final[Sequence[intermediate.EnumerationLiteral]]

    # fmt: off
    @require(
        lambda enumeration, literals:
        all(
            id(literal) in enumeration.literal_id_set
            for literal in literals
        )
    )
    # fmt: on
    def __init__(
            self,
            enumeration: intermediate.Enumeration,
            literals: Sequence[intermediate.EnumerationLiteral],
    ) -> None:
        """Initialize with the given values."""
        self.enumeration = enumeration
        self.literals = literals

    def __repr__(self) -> str:
        """Represent the constraint with the pattern."""
        return f"<{self.__class__.__name__} at 0x{id(self):x}>"

    def equals(self, other: Optional["SetOfPrimitivesConstraint"]) -> bool:
        """Return true if the other constraint equals semantically ours."""
        if other is None:
            return False

        return (
                self.a_type == other.a_type
                and len(self.literals) == len(other.literals)
                and all(
            id(that_literal) == id(other_literal)
            for that_literal, other_literal in zip(self.literals, other.literals)
        )
        )


class Constraints:
    """
    Represent all the inferred constraints for a value.

    The constraints coming from the constrained primitives are in-lined and hence also
    included in this representation.
    """

    len_constraint: Final[Optional[LenConstraint]]
    patterns: Final[Optional[Sequence[PatternConstraint]]]
    set_of_primitives: Final[Optional[SetOfPrimitivesConstraint]]
    set_of_enumeration_literals: Final[Optional[SetOfEnumerationLiteralsConstraint]]

    @require(
        lambda patterns:
        not (patterns is not None) or len(patterns) > 0
    )
    def __init__(
            self,
            len_constraint: Optional[LenConstraint] = None,
            patterns: Optional[Sequence[PatternConstraint]] = None,
            set_of_primitives: Optional[SetOfPrimitivesConstraint] = None,
            set_of_enumeration_literals: Optional[
                SetOfEnumerationLiteralsConstraint
            ] = None
    ) -> None:
        """Initialize with the given values."""
        self.len_constraint = len_constraint
        self.patterns = patterns
        self.set_of_primitives = set_of_primitives
        # fmt: off
        self.set_of_enumeration_literals = (
            set_of_enumeration_literals
        )
        # fmt: on

    def is_empty(self) -> bool:
        """Return True if no constraints are set."""
        return (
                self.len_constraint is None
                and self.patterns is None
                and self.set_of_primitives is None
                and self.set_of_enumeration_literals is None
        )

    def update_steps_to(self, other: "Constraint") -> "Constraint":
        """
        Identify what would need to be changed in self to equal ``other``.

        We assume that None on any of the constraints means no change.

        If a constraint is set in ``other``, but not available in ``self``, we
        raise a ValueError.
        """
        len_constraint: Optional[LenConstraint] = None

        if other.len_constraint is not None and self.len_constraint is not None:
            if not self.len_constraint.equals(other.len_constraint):
                len_constraint = self.len_constraint

        elif other.len_constraint is not None and self.len_constraint is None:
            raise ValueError(
                "This instance of constraints specifies no length constraint, while "
                f"the other does: {other.len_constraint}; we can not compute the "
                f"update steps this way."
            )

        elif other.len_constraint is None and self.len_constraint is not None:
            len_constraint = self.len_constraint

        elif other.len_constraint is None and self.len_constraint is None:
            pass

        else:
            raise AssertionError("Unexpected execution path")

        # TODO: implement this for all the other constraints -- then go back to json schema generator
        # TODO:  and fix it -- we need to handle the regression_when_len_constraints_on_inherited_property
        # TODO:  --> we ignore the constraints which are tightened in the child class!
        # TODO:  --> hence we need to check which constraints from the parent differ in the child.


#: Represent the constraints inferred for the given value in a class.
ConstraintsByValue: TypeAlias = Mapping[
    intermediate.TypeAnnotationUnion,
    Constraints
]
