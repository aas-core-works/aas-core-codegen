from enum import Enum
from typing import List, Optional, Sequence

from icontract import DBC, invariant


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"


class Item(DBC):
    text: str
    maybe_text: Optional[str]
    maybe_kind: Optional[Kind]
    texts: List[str]
    maybe_texts: Optional[List[str]]

    def __init__(
        self,
        text: str,
        texts: List[str],
        maybe_text: Optional[str] = None,
        maybe_kind: Optional[Kind] = None,
        maybe_texts: Optional[List[str]] = None,
    ) -> None:
        self.text = text
        self.texts = texts
        self.maybe_text = maybe_text
        self.maybe_kind = maybe_kind
        self.maybe_texts = maybe_texts


@verification
def set_text(item: Mutable["Item"], text: str) -> bool:
    """Check the assignment to a property."""
    item.text = text
    return True


@verification
def set_maybe_text(item: Mutable["Item"], text: str) -> bool:
    """Check the assignment of a value to an optional property."""
    item.maybe_text = text
    return True


@verification
def copy_maybe_text_and_set_maybe_kind(item: Mutable["Item"], other: Item) -> bool:
    """Check the assignment of an optional value, and of an enumeration literal."""
    item.maybe_text = other.maybe_text
    item.maybe_kind = Kind.Alpha
    return True


@verification
def set_text_through_alias(item: Mutable["Item"], text: str) -> bool:
    """Check the assignment to a property through a local alias of the object."""
    alias = item
    alias.text = text
    return True


@verification
def set_texts(item: Mutable["Item"], texts: Sequence[str]) -> bool:
    """Check the assignment of a copy of a list to a property."""
    item.texts = texts[:]
    return True


@verification
def set_first_and_last_text(item: Mutable["Item"], text: str) -> bool:
    """Check the assignment to the items of a list, including a negative index."""
    item.texts[0] = text
    item.texts[-1] = text
    return True


@verification
def set_text_through_list_alias(item: Mutable["Item"], text: str) -> bool:
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
def replace_first_item(items: List[Item], item: Mutable["Item"]) -> bool:
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


@verification
def fill_texts(texts: List[str], text: str) -> bool:
    """Check the mutation of a list argument in place."""
    for i in range(0, len(texts)):
        texts[i] = text

    return True


@verification
def fill_texts_of_item(item: Mutable["Item"], text: str) -> bool:
    """Check passing a property as a mutable list argument."""
    return fill_texts(item.texts, text)


@verification
def fill_texts_through_alias(item: Mutable["Item"], text: str) -> bool:
    """Check passing a local alias of a list as a mutable list argument."""
    texts = item.texts
    return fill_texts(texts, text)


@verification
def fill_texts_of_argument(texts: List[str], text: str) -> bool:
    """Check passing a list argument on as a mutable list argument."""
    return fill_texts(texts, text)


@verification
def rename(item: Mutable["Item"], text: str) -> bool:
    """Check the mutation of an object argument."""
    item.text = text
    return True


@verification
def rename_all(items: List[Item], text: str) -> bool:
    """Check passing the loop variable as a mutable object argument."""
    result = True
    for item in items:
        result = rename(item, text)

    return result


@verification
def set_first_texts_of_lists(lists: List[List[str]], text: str) -> bool:
    """Check the mutation of the inner lists through a loop variable."""
    for texts in lists:
        texts[0] = text

    return True


@verification
def set_first_texts_in_sibling_loops(
    items: List[Item], others: List[Item], text: str
) -> bool:
    """Check the same name defined in sibling loops, both as mutable aliases."""
    for item in items:
        texts = item.texts
        texts[0] = text

    for other in others:
        texts = other.texts
        texts[0] = text

    return True


@verification
def text_copy_is_independent(item: Mutable["Item"], text: str) -> bool:
    """Check that a local copy of a string is not changed by the setter."""
    old = item.text
    item.text = text
    return old != item.text


@verification
def number_copy_is_independent(numbers: List[int]) -> bool:
    """Check that a local copy of a number is not changed by the list mutation."""
    first = numbers[0]
    numbers[0] = first + 1
    return first + 1 == numbers[0]


@verification
def set_maybe_texts(item: Mutable["Item"], texts: Sequence[str]) -> bool:
    """Check the assignment of a copy of a list to an optional property."""
    item.maybe_texts = texts[:]
    return True


@verification
def set_maybe_item(something: Mutable["Something"], item: Mutable["Item"]) -> bool:
    """Check the assignment of an object to an optional property."""
    something.maybe_item = item
    return True


@verification
def set_text_of_rebound_alias(
    item: Mutable["Item"], other: Mutable["Item"], text: str
) -> bool:
    """Check the re-assignment of a local alias of an object."""
    alias = item
    alias = other
    alias.text = text
    return True


@verification
def first_text_through_alias_is(item: Item, text: str) -> bool:
    """Check the read-only alias of a list property."""
    texts = item.texts
    return texts[0] == text


@verification
def texts_are_not_empty(items: Sequence[Item]) -> bool:
    """Check that no text is empty through a read-only list argument."""
    for item in items:
        for text in item.texts:
            if text == "":
                return False

    return True


@invariant(lambda self: texts_are_not_empty(self.items), "Texts are not empty")
class Something(DBC):
    items: List[Item]
    maybe_item: Optional[Item]

    def __init__(self, items: List[Item], maybe_item: Optional[Item] = None) -> None:
        self.items = items
        self.maybe_item = maybe_item


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
