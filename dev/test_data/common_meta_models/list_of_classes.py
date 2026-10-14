from enum import Enum
from typing import List, Optional, Sequence

from icontract import invariant


@abstract
@serialization(with_model_type=True)
class Abstract_item:
    pass


class Some_item(Abstract_item):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


@verification
def items_are_some(items: Sequence[Abstract_item]) -> bool:
    """Check a read-only list of base-class instances."""
    return all(isinstance(item, Some_item) for item in items)


@verification
def some_items_are_some(items: Sequence[Some_item]) -> bool:
    """Pass a list of descendants to a base-class list parameter."""
    return items_are_some(items)


@verification
def optional_some_items_are_some(items: Optional[Sequence[Some_item]]) -> bool:
    """Preserve an optional descendant list passed to an optional parameter."""
    return optional_items_are_some(items)


@verification
def optional_items_are_some(items: Optional[Sequence[Abstract_item]]) -> bool:
    """Check a possibly missing read-only list of base-class instances."""
    return items is None or items_are_some(items)


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
