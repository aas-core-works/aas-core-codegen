"""Provide data structures for the constraint inferences."""
from typing import Mapping, Sequence, Optional

from icontract import require

from aas_core_codegen import intermediate


class LenConstraint:
    """
    Represent the inferred constraint on the ``len`` of something.

    Both bounds are inclusive: ``min_value ≤ len ≤ max_value``.
    """

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

    def copy(self) -> "LenConstraint":
        """Create a copy of the self."""
        return LenConstraint(min_value=self.min_value, max_value=self.max_value)

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"min_value={self.min_value!r}, max_value={self.max_value!r})"
        )


class PatternConstraint:
    """Constrain a string to comply to a regular expression."""

    def __init__(self, pattern: str) -> None:
        """Initialize with the given values."""
        self.pattern = pattern

    def __repr__(self) -> str:
        """Represent the constraint with the pattern."""
        return (
            f"<{self.__class__.__name__} at 0x{id(self):x} "
            f"with pattern={self.pattern!r}>"
        )


class SetOfPrimitivesConstraint:
    """Constrain a primitive value to be a member of a pre-defined set of values."""

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


class SetOfEnumerationLiteralsConstraint:
    """Constrain a value to be a member of a pre-defined set of values."""

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


class ConstraintsByProperty:
    """
    Represent all the inferred property constraints of one of our types.

    The constraints coming from the constrained primitives are in-lined and hence also
    included in this representation.
    """

    def __init__(
        self,
        len_constraints_by_property: Mapping[intermediate.Property, LenConstraint],
        patterns_by_property: Mapping[
            intermediate.Property, Sequence[PatternConstraint]
        ],
        set_of_primitives_by_property: Mapping[
            intermediate.Property, SetOfPrimitivesConstraint
        ],
        set_of_enumeration_literals_by_property: Mapping[
            intermediate.Property, SetOfEnumerationLiteralsConstraint
        ],
    ) -> None:
        """Initialize with the given values."""
        self.len_constraints_by_property = len_constraints_by_property
        self.patterns_by_property = patterns_by_property
        self.set_of_primitives_by_property = set_of_primitives_by_property
        # fmt: off
        self.set_of_enumeration_literals_by_property = (
            set_of_enumeration_literals_by_property
        )
        # fmt: on
