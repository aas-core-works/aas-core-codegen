"""
Test that a public generic verification function can not call an internal one.

The public generic verification functions are templates defined in the C++ header,
while the internal verification functions are declared only in the implementation
file.
"""

from typing import List, Sequence

from icontract import DBC, invariant


@abstract
@serialization(with_model_type=True)
class Item(DBC):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class Some_item(Item, DBC):
    def __init__(self, name: str) -> None:
        Item.__init__(self, name)


@verification
def _is_named(item: Item) -> bool:
    return len(item.name) > 0


@verification
def items_are_named(items: Sequence[Item]) -> bool:
    return all(_is_named(item) for item in items)


@invariant(
    lambda self: items_are_named(self.items),
    "The items must be named.",
)
class Container(DBC):
    items: List[Some_item]

    def __init__(self, items: List[Some_item]) -> None:
        self.items = items


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
