"""
Check the lists of primitives.

We check the list literals and the local lists built with ``append``.
The lengths are appended to and put in a list literal on purpose, since
the targets represent them differently from our integers.

We also check the membership ``in`` a list of primitives, passed as a read-only
and as an optional argument, built locally with ``append`` or given as a list
literal, and the membership ``in`` a string, *i.e.*, the check for a sub-string.
The integer literals and the lengths are looked up in the list of integers on
purpose, since the targets represent them differently from the items.
"""
from typing import List, Optional, Sequence

from icontract import DBC, invariant


@verification
def is_small_prime(number: int) -> bool:
    """Check whether :paramref:`number` is a prime smaller than 10."""
    for prime in [2, 3, 5, 7]:
        if prime == number:
            return True

    return False


@verification
def count_and_lengths_of(texts: Sequence[str]) -> List[int]:
    """Give the number of :paramref:`texts` followed by their lengths."""
    result = [len(texts)]
    for text in texts:
        result.append(len(text))

    return result


@verification
def positives_of(numbers: Sequence[int]) -> List[int]:
    """Give the positive :paramref:`numbers` in the same order."""
    result: List[int] = []
    for number in numbers:
        if number > 0:
            result.append(number)

    return result


@verification
def ints_are_unique(numbers: Sequence[int]) -> bool:
    """Check that :paramref:`numbers` are unique with a local list of the seen."""
    seen: List[int] = []
    for number in numbers:
        if number in seen:
            return False

        seen.append(number)

    return True


@verification
def is_separator(text: str) -> bool:
    """Check whether :paramref:`text` is one of the separators."""
    return text in [".", ",", ";"]


@verification
def is_in_ints(number: int, numbers: Sequence[int]) -> bool:
    """Check whether :paramref:`number` is in :paramref:`numbers`."""
    return number in numbers


@verification
def is_in_optional_strings(text: str, texts: Optional[Sequence[str]]) -> bool:
    """Check whether :paramref:`text` is in :paramref:`texts`, if specified."""
    if texts is None:
        return False

    return text in texts


@verification
def contains_dot(text: str) -> bool:
    """Check whether :paramref:`text` contains a dot."""
    return "." in text


@invariant(
    lambda self: all(not is_separator(text) for text in self.some_strings),
    "Some strings must not be separators.",
)
@invariant(
    lambda self: ints_are_unique(self.some_ints),
    "Some ints must be unique.",
)
@invariant(
    lambda self: all(not contains_dot(text) for text in self.some_strings),
    "Strings must not contain dots.",
)
@invariant(
    lambda self: not is_in_optional_strings("", self.some_strings),
    "Strings must not contain an empty string.",
)
@invariant(
    lambda self: not (-1.0 in self.some_floats),
    "Floats must not contain minus one.",
)
@invariant(
    lambda self: not is_in_ints(len(self.some_strings), self.some_ints),
    "Ints must not contain the number of strings.",
)
@invariant(
    lambda self: not (0 in self.some_ints),
    "Ints must not contain zero.",
)
@invariant(
    lambda self: len(positives_of(self.some_ints)) <= 1,
    "At most one of some ints must be positive.",
)
@invariant(
    lambda self: all(
        number <= 10 for number in count_and_lengths_of(self.some_strings)
    ),
    "There must be at most 10 strings of at most 10 characters each.",
)
@invariant(
    lambda self: all(not is_small_prime(number) for number in self.some_ints),
    "Some ints must not contain small primes.",
)
class Something(DBC):
    some_bools: List[bool]
    some_ints: List[int]
    some_floats: List[float]
    some_strings: List[str]
    some_bytes: List[bytearray]

    def __init__(
        self,
        some_bools: List[bool],
        some_ints: List[int],
        some_floats: List[float],
        some_strings: List[str],
        some_bytes: List[bytearray],
    ) -> None:
        self.some_bools = some_bools
        self.some_ints = some_ints
        self.some_floats = some_floats
        self.some_strings = some_strings
        self.some_bytes = some_bytes


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
