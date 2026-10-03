"""
Check the transpilation of the methods.

The invariants are verified only in the verification module, and never enforced
after the method calls.
"""
from enum import Enum
from typing import List, Optional

from icontract import DBC, invariant


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"


@verification
def reset_and_check(
    item: Mutable["Item"], other: Mutable["Item"], numbers: List[int]
) -> bool:
    """Check calling the methods which mutate the instance and the arguments."""
    item.reset()
    item.fill_numbers(numbers)
    item.copy_count_to(other)
    return item.count == 0 and item.is_empty()


@invariant(lambda self: self.parity() <= 1, "Parity is either zero or one.")
@invariant(lambda self: self.total_length() <= 20, "Total length is at most 20.")
@invariant(lambda self: not self.has_text("forbidden"), "No text is forbidden.")
@invariant(
    lambda self: self.is_count_within(len(self.texts)),
    "Count is at most the number of texts.",
)
@abstract
@serialization(with_model_type=True)
class Item(DBC):
    texts: List[str]
    count: int
    kind: Optional[Kind]

    @non_mutating
    def has_text(self, text: str) -> bool:
        """Check that :paramref:`text` is among the texts."""
        return any(existing == text for existing in self.texts)

    @non_mutating
    def total_length(self) -> int:
        """Sum up the lengths of the texts."""
        result = 0
        for text in self.texts:
            result = result + len(text)

        return result

    @non_mutating
    def is_count_within(self, limit: int) -> bool:
        """Check that the count does not exceed :paramref:`limit`."""
        return self.count <= limit

    @non_mutating
    def is_count_between(self, low: int, high: int) -> bool:
        """Check that the count is between :paramref:`low` and :paramref:`high`."""
        return low <= self.count and self.count <= high

    @non_mutating
    def is_empty(self) -> bool:
        """Check that there are no texts, calling another method on ``self``."""
        return len(self.texts) == 0 and self.total_length() == 0

    # NOTE (mristin):
    # The leading underscore signals a protected method, which is not part of
    # the interface.
    @non_mutating
    def _doubled_count(self) -> int:
        """Double the count."""
        return self.count + self.count

    @non_mutating
    def parity(self) -> int:
        """Compute the parity of the count with the modulo as in Python."""
        return abs(self.count % 2)

    @non_mutating
    def fill_numbers(self, numbers: List[int]) -> None:
        """Overwrite all the :paramref:`numbers` with the count."""
        for i in range(0, len(numbers)):
            numbers[i] = self.count

    @non_mutating
    def copy_count_to(self, other: Mutable["Item"]) -> None:
        """Copy the count to :paramref:`other`."""
        other.count = self.count

    def fill_texts(self, text: str) -> None:
        """Replace all the texts with :paramref:`text`."""
        for i in range(0, len(self.texts)):
            self.texts[i] = text

    def reset(self) -> None:
        """Reset the texts, the count and the kind."""
        self.fill_texts("")
        self.count = 0
        self.kind = Kind.Alpha

    def increment_count(self) -> int:
        """Increment the count, and return its double."""
        self.count = self.count + 1
        return self._doubled_count()

    def __init__(
        self, texts: List[str], count: int, kind: Optional[Kind] = None
    ) -> None:
        self.texts = texts
        self.count = count
        self.kind = kind


class First(Item):
    def __init__(
        self, texts: List[str], count: int, kind: Optional[Kind] = None
    ) -> None:
        Item.__init__(self, texts, count, kind)


@invariant(lambda self: len(self.prefix()) <= 3, "Prefix is at most three long.")
class Second(Item):
    note: str

    @non_mutating
    def prefix(self) -> str:
        """Return the first three characters of the note."""
        return self.note[:3]

    def __init__(
        self,
        texts: List[str],
        count: int,
        note: str,
        kind: Optional[Kind] = None,
    ) -> None:
        Item.__init__(self, texts, count, kind)
        self.note = note


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
