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
            f"LenConstraint(min_value={self.min_value!r}, max_value={self.max_value!r})"
        )


class PatternConstraint:
    """Constrain a string to comply to a regular expression."""

    def __init__(self, pattern: str) -> None:
        """Initialize with the given values."""
        self.pattern = pattern


class ConstraintsByProperty:
    """
    Represent all the inferred property constraints of a symbol.

    The constraints coming from the constrained primitives are in-lined and hence also
    included in this representation.
    """

    def __init__(
        self,
        len_constraints_by_property: Mapping[intermediate.Property, LenConstraint],
        patterns_by_property: Mapping[
            intermediate.Property, Sequence[PatternConstraint]
        ],
    ) -> None:
        """Initialize with the given values."""
        self.len_constraints_by_property = len_constraints_by_property
        self.patterns_by_property = patterns_by_property
