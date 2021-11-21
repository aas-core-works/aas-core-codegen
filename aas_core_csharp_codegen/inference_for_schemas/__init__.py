"""
Infer constraints for schemas (JSON Schema, XSD *etc.*) based on the invariants.

Mind that many constraints *can not* be modeled by the schemas (*e.g.*, lower bound
smaller than the upper bound in a range), and are thus not inferred.
"""
from typing import Optional, List, Union, MutableMapping

from icontract import require

from aas_core_csharp_codegen import intermediate


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


class Pattern(Constraint):
    """
    Represent the expected regular expression.

    Please control yourself that the pattern matches your schema implementation in terms
    of special symbols and characters.
    """

    def __init__(self, value: str) -> None:
        """Initialize with the given values."""
        self.value = value



def infer(
        symbol: Union[intermediate.Interface, intermediate.Class],
        symbol_table: intermediate.SymbolTable
) -> MutableMapping[intermediate.Property, List[Constraint]]:
    """Infer the constraints for each property based on the invariants."""
    # TODO: continue here
    # TODO: do not make this quadratic — make a single loop through properties!
    # TODO: refactor shacl.py