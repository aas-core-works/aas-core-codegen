from enum import Enum
from typing import List, Optional

from icontract import DBC


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"


class Item(DBC):
    text: str
    maybe_text: Optional[str]
    maybe_kind: Optional[Kind]
    texts: List[str]

    def __init__(
        self,
        text: str,
        texts: List[str],
        maybe_text: Optional[str] = None,
        maybe_kind: Optional[Kind] = None,
    ) -> None:
        self.text = text
        self.texts = texts
        self.maybe_text = maybe_text
        self.maybe_kind = maybe_kind


@verification
def set_text(item: Item, text: str) -> bool:
    """Check the assignment to a property."""
    item.text = text
    return True


@verification
def set_maybe_text(item: Item, text: str) -> bool:
    """Check the assignment of a value to an optional property."""
    item.maybe_text = text
    return True


@verification
def copy_maybe_text_and_set_maybe_kind(item: Item, other: Item) -> bool:
    """Check the assignment of an optional value, and of an enumeration literal."""
    item.maybe_text = other.maybe_text
    item.maybe_kind = Kind.Alpha
    return True


@verification
def set_text_through_alias(item: Item, text: str) -> bool:
    """Check the assignment to a property through a local alias of the object."""
    alias = item
    alias.text = text
    return True


@verification
def set_texts(item: Item, texts: List[str]) -> bool:
    """Check the assignment of a list to a property."""
    item.texts = texts
    return True


@verification
def set_first_and_last_text(item: Item, text: str) -> bool:
    """Check the assignment to the items of a list, including a negative index."""
    item.texts[0] = text
    item.texts[-1] = text
    return True


@verification
def set_text_through_list_alias(item: Item, text: str) -> bool:
    """Check the assignment to an item through a local alias of the list."""
    texts = item.texts
    texts[1] = text
    return True


@verification
def set_numbers(numbers: List[int], number: int) -> bool:
    """Check the assignment to the items of a list parameter."""
    numbers[0] = number
    numbers[-2] = numbers[-1] + 1
    return True


@verification
def set_nested_text(items: List[Item], text: str) -> bool:
    """Check the assignment to the items of a list nested in a list."""
    items[0].texts[-1] = text
    items[-1].text = text
    return True


@verification
def replace_first_item(items: List[Item], item: Item) -> bool:
    """Check the assignment of an object to an item of a list."""
    items[0] = item
    return True


@verification
def set_texts_in_loops(items: List[Item], text: str) -> bool:
    """Check the assignment to the properties of the objects iterated over."""
    for item in items:
        item.text = text

    for i in range(0, len(items)):
        items[i].texts[0] = text

    return True


class Something(DBC):
    items: List[Item]

    def __init__(self, items: List[Item]) -> None:
        self.items = items


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
