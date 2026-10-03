"""
Check the nested lists, tuples and sets.

The lists, the tuples and the sets nest at any depth, while ``Optional`` is
allowed only at the top of a type annotation. The items of the sets stay
scalar.

We nest the primitives, the constrained primitives, the enumerations,
the polymorphic classes and the named unions so that every target descends into
them at every depth: in the de/serialization, the verification, the iteration
and the enhancing. The items of the sets are picked so that a wrong order of
the serialized items shows.

We also check the transpilation of the nested collections in the invariants and
the verification functions: the nested for-loops, the chained indexing,
``len``, ``in``, ``all`` and ``any``, the read-only and the mutable arguments,
and the local variables.
"""
from enum import Enum
from typing import AbstractSet, Final, List, Optional, Sequence, Set, Tuple, Union

from icontract import DBC, invariant

from aas_core_meta.marker import abstract, serialization


class Color(Enum):
    Red = "red"
    Green = "green"
    Blue = "blue"


@invariant(lambda self: self > 0, "Positive int must be positive.")
class Positive_int(int, DBC):
    """Represent a positive integer."""


@invariant(lambda self: len(self) > 0, "Code must not be empty.")
class Code(str, DBC):
    """Represent a non-empty code."""


@abstract
@serialization(with_model_type=True)
class Abstract_item(DBC):
    pass


@invariant(lambda self: len(self.name) > 0, "Name must not be empty.")
class Some_item(Abstract_item):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class Another_item(Abstract_item):
    serial_number: int

    def __init__(self, serial_number: int) -> None:
        self.serial_number = serial_number


Some_union = Union[Some_item, Another_item]


@verification
def grid_is_rectangular(grid: Sequence[Sequence[int]]) -> bool:
    """Check that all the rows of :paramref:`grid` are equally long."""
    if len(grid) < 1:
        return True

    first_row: Final[Sequence[int]] = grid[0]
    for row in grid:
        if len(row) != len(first_row):
            return False

    return True


@verification
def colors_are_disjoint(sets_of_colors: Sequence[AbstractSet[Color]]) -> bool:
    """Check that no color appears in more than one set."""
    seen: Set[Color] = set()
    for colors in sets_of_colors:
        for color in colors:
            if color in seen:
                return False

            seen.add(color)

    return True


@verification
def some_label_is_known(
    rows_of_pairs: Sequence[Sequence[Tuple[Positive_int, AbstractSet[str]]]],
    label: str,
) -> bool:
    """Check that :paramref:`label` is in some set of the nested pairs."""
    return any(any(label in pair[1] for pair in row) for row in rows_of_pairs)


@verification
def reset_corner(grid: List[List[int]]) -> bool:
    """Reset the first cell of the first row of :paramref:`grid`, if any."""
    if len(grid) > 0 and len(grid[0]) > 0:
        grid[0][0] = 0

    return True


@invariant(
    lambda self: grid_is_rectangular(self.grid),
    "Grid must be rectangular.",
)
@invariant(
    lambda self: all(len(row) > 0 for row in self.grid),
    "Rows of the grid must not be empty.",
)
@invariant(
    lambda self: all(
        all(len(pair[1]) > 0 for pair in row) for row in self.rows_of_pairs
    ),
    "Sets of labels must not be empty.",
)
@invariant(
    lambda self: some_label_is_known(self.rows_of_pairs, "known"),
    "Some set of labels must contain the label 'known'.",
)
@invariant(
    lambda self: len(self.mixed[0]) > 0,
    "Items of mixed must not be empty.",
)
@invariant(
    lambda self: self.mixed[2][0] >= 0,
    "Number of mixed must not be negative.",
)
@invariant(
    lambda self: not (Color.Red in self.mixed[1]),
    "Colors of mixed must not contain red.",
)
@invariant(
    lambda self: colors_are_disjoint(self.sets_of_colors),
    "Sets of colors must be disjoint.",
)
@invariant(
    lambda self: not (self.optional_grid_of_items is not None)
    or all(len(row) > 0 for row in self.optional_grid_of_items),
    "Rows of the optional grid of items must not be empty.",
)
class Something(DBC):
    #: Test a list of lists of primitives
    grid: List[List[int]]

    #: Test a list of lists of tuples, mixing a constrained primitive with a set
    rows_of_pairs: List[List[Tuple[Positive_int, Set[str]]]]

    #: Test a tuple of a list of polymorphic instances, a set of enumeration
    #: literals and a nested tuple
    mixed: Tuple[List[Abstract_item], Set[Color], Tuple[int, Code]]

    #: Test a list of sets of enumeration literals
    sets_of_colors: List[Set[Color]]

    #: Test a list of lists of named unions
    grid_of_unions: List[List[Some_union]]

    #: Test an optional list of lists of polymorphic instances
    optional_grid_of_items: Optional[List[List[Abstract_item]]]

    def __init__(
        self,
        grid: List[List[int]],
        rows_of_pairs: List[List[Tuple[Positive_int, Set[str]]]],
        mixed: Tuple[List[Abstract_item], Set[Color], Tuple[int, Code]],
        sets_of_colors: List[Set[Color]],
        grid_of_unions: List[List[Some_union]],
        optional_grid_of_items: Optional[List[List[Abstract_item]]] = None,
    ) -> None:
        self.grid = grid
        self.rows_of_pairs = rows_of_pairs
        self.mixed = mixed
        self.sets_of_colors = sets_of_colors
        self.grid_of_unions = grid_of_unions
        self.optional_grid_of_items = optional_grid_of_items


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
