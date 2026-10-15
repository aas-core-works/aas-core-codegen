"""
Check the lists of primitives.

We also check the list literals and the local lists built with ``append``.
The lengths are appended to and put in a list literal on purpose, since
the targets represent them differently from our integers.
"""
from typing import List, Sequence

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
