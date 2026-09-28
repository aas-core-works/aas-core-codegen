from enum import Enum
from typing import List, Sequence

from icontract import DBC, invariant


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"


class Item(DBC):
    texts: List[str]

    def __init__(self, texts: List[str]) -> None:
        self.texts = texts


@verification
def first_text_is_not_empty(texts: Sequence[str]) -> bool:
    """Check the for-each with an unconditional early return."""
    for text in texts:
        return len(text) > 0

    return True


@verification
def no_number_is_zero(numbers: Sequence[int]) -> bool:
    """Check the for-each with an early return in a switch."""
    for number in numbers:
        if number == 0:
            return False

    return True


@verification
def no_number_is_minus_one(numbers: Sequence[int]) -> bool:
    """Check the for-range with a variable defined in the body of the loop."""
    for i in range(0, len(numbers)):
        number = numbers[i]
        if number == -1:
            return False

    return True


@verification
def no_number_after_the_first_is_one(numbers: Sequence[int]) -> bool:
    """Check the for-range which does not start at zero."""
    for i in range(1, len(numbers)):
        if numbers[i] == 1:
            return False

    return True


@verification
def sum_is_small(numbers: Sequence[int]) -> bool:
    """Check the for-each which assigns to a variable defined before the loop."""
    total = 0
    for number in numbers:
        total = total + number

    return total < 100


@verification
def no_item_has_an_empty_text(items: Sequence[Item]) -> bool:
    """Check the nested for-each loops."""
    for item in items:
        texts = item.texts
        for text in texts:
            if text == "":
                return False

    return True


@verification
def is_neither_thirteen_nor_unlucky(texts: Sequence[str]) -> bool:
    """Check the loop variable re-used in a sibling loop."""
    for x in texts:
        if x == "thirteen":
            return False

    for x in texts:
        if x == "unlucky":
            return False

    return True


@verification
def alpha_has_no_negative_numbers(kind: Kind, numbers: Sequence[int]) -> bool:
    """Check the for-each in a switch branch."""
    if kind == Kind.Alpha:
        for number in numbers:
            if number == -2:
                return False

    return True


@verification
def sum_of_odd_numbers_is_small(numbers: Sequence[int]) -> bool:
    """Check the for-each with a continue in a switch followed by statements."""
    total = 0
    for number in numbers:
        if number % 2 == 0:
            continue

        total = total + number

    return total < 50


@verification
def items_are_few_and_texts_expected(items: Sequence[Item]) -> bool:
    """Check the continue in all the branches of a switch in a nested for-range."""
    count = 0
    for item in items:
        for i in range(0, len(item.texts)):
            text = item.texts[i]
            if text == "unexpected":
                return False
            elif text == "a" or text == "b":
                continue
            else:
                continue

        count = count + 1

    return count < 3


@verification
def numbers_before_stop_are_few(numbers: Sequence[int]) -> bool:
    """Check the for-each with a break in a switch followed by statements."""
    count = 0
    for number in numbers:
        if number == -50:
            break

        count = count + 1

    return count < 5


@verification
def weights_before_end_are_small(numbers: Sequence[int]) -> bool:
    """Check the break in a chain of if and elif which compares a single subject."""
    total = 0
    for number in numbers:
        if number == 3:
            total = total + 1
        elif number == 4 or number == 5:
            total = total + 2
        elif number in (-50, -51):
            break
        else:
            total = total + 10

    return total < 20


@verification
def texts_before_stop_are_few(kind: Kind, items: Sequence[Item]) -> bool:
    """Check the break in the nested branches of a switch in a nested for-range."""
    count = 0
    for item in items:
        for i in range(0, len(item.texts)):
            if kind == Kind.Alpha:
                if item.texts[i] == "stop":
                    break
            else:
                if len(item.texts[i]) > 10:
                    break

            count = count + 1

    return count < 3


@invariant(
    lambda self: first_text_is_not_empty(self.texts),
    "The first text must not be empty",
)
@invariant(lambda self: no_number_is_zero(self.numbers), "No number is zero")
@invariant(lambda self: no_number_is_minus_one(self.numbers), "No number is minus one")
@invariant(
    lambda self: no_number_after_the_first_is_one(self.numbers),
    "No number after the first is one",
)
@invariant(lambda self: sum_is_small(self.numbers), "Sum of numbers is small")
@invariant(
    lambda self: no_item_has_an_empty_text(self.items),
    "No item has an empty text",
)
@invariant(
    lambda self: is_neither_thirteen_nor_unlucky(self.texts),
    "Neither thirteen nor unlucky",
)
@invariant(
    lambda self: alpha_has_no_negative_numbers(self.kind, self.numbers),
    "Alpha has no minus two",
)
@invariant(
    lambda self: sum_of_odd_numbers_is_small(self.numbers),
    "Sum of odd numbers is small",
)
@invariant(
    lambda self: items_are_few_and_texts_expected(self.items),
    "Items are few and their texts expected",
)
@invariant(
    lambda self: numbers_before_stop_are_few(self.numbers),
    "Numbers before the stop are few",
)
@invariant(
    lambda self: weights_before_end_are_small(self.numbers),
    "Weights before the end are small",
)
@invariant(
    lambda self: texts_before_stop_are_few(self.kind, self.items),
    "Texts before the stop are few",
)
class Something(DBC):
    kind: Kind
    numbers: List[int]
    texts: List[str]
    items: List[Item]

    def __init__(
        self,
        kind: Kind,
        numbers: List[int],
        texts: List[str],
        items: List[Item],
    ) -> None:
        self.kind = kind
        self.numbers = numbers
        self.texts = texts
        self.items = items


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
