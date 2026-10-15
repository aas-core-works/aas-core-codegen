from enum import Enum
from typing import List, Sequence

from icontract import invariant


@abstract
@serialization(with_model_type=True)
class Abstract_item:
    pass


class Some_item(Abstract_item):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class Another_item(Abstract_item):
    serial_number: int

    def __init__(self, serial_number: int) -> None:
        self.serial_number = serial_number


# NOTE (mristin):
# This class does not inherit from any other class nor does it have any descendants.
# This allows us to test the edge case where a class does not require a model type for
# serialization.
class Simple:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


@verification
def names_of(simples: Sequence[Simple]) -> List[str]:
    """Give the names of :paramref:`simples` in the same order."""
    names: List[str] = []
    for simple in simples:
        names.append(simple.name)

    return names


@verification
def simples_with(simple: Simple, simples: Sequence[Simple]) -> List[Simple]:
    """Give :paramref:`simple` followed by :paramref:`simples`."""
    result = [simple]
    for other in simples:
        result.append(other)

    return result


@verification
def some_items_of(items: Sequence[Abstract_item]) -> List[Abstract_item]:
    """
    Give the instances of :class:`Some_item` among :paramref:`items`.

    The appended items are narrowed down to :class:`Some_item`, while the list
    holds :class:`Abstract_item`'s.
    """
    result: List[Abstract_item] = []
    for item in items:
        if isinstance(item, Some_item):
            result.append(item)

    return result


@verification
def is_in_simples(simple: Simple, simples: Sequence[Simple]) -> bool:
    """
    Check whether :paramref:`simple` is in :paramref:`simples`.

    The targets compare the instances of the classes by their references.
    """
    return simple in simples


@verification
def is_in_local_copy_of_simples(simple: Simple, simples: Sequence[Simple]) -> bool:
    """
    Check whether :paramref:`simple` is in a local copy of :paramref:`simples`.

    The local copy is built with ``append``, and holds the same instances as
    :paramref:`simples`.
    """
    copied: List[Simple] = []
    for other in simples:
        copied.append(other)

    return simple in copied


@invariant(
    lambda self: all(
        is_in_local_copy_of_simples(simple, self.some_simples)
        for simple in self.some_simples
    ),
    "Each of some simples must be in a local copy of some simples.",
)
@invariant(
    lambda self: not is_in_simples(self.item, self.some_simples),
    "Item must not be one of some simples.",
)
@invariant(
    lambda self: len(some_items_of(self.some_items)) <= 1,
    "At most one of some items must be a some item.",
)
@invariant(
    lambda self: len(simples_with(self.item, self.some_simples))
    == len(self.some_simples) + 1,
    "Item followed by some simples must be one longer than some simples.",
)
@invariant(
    lambda self: all(len(name) > 0 for name in names_of(self.some_simples)),
    "Names of some simples must not be empty.",
)
class Something:
    # NOTE (mristin):
    # The property ``item`` comes before the lists of classes on purpose, so that
    # its local variable is visible in the lambdas which transform the list items
    # in the generated code, *e.g.*, in the Java enhancing. The lambda parameters
    # must not collide with it.
    item: Simple
    some_items: List[Abstract_item]
    some_simples: List[Simple]

    def __init__(
        self,
        item: Simple,
        some_items: List[Abstract_item],
        some_simples: List[Simple],
    ) -> None:
        self.item = item
        self.some_items = some_items
        self.some_simples = some_simples


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
