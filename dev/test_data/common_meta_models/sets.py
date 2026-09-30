"""
Check the transpilation of the sets of primitives and enumeration literals.

We check the local sets created with ``set()``, filled with ``add`` and queried
with ``in``, the sets passed as read-only (``AbstractSet``) and as mutable
(``Set``) arguments, the optional sets, and the constant sets passed as arguments.

We also check the iteration over the sets, their ``intersection``, ``difference``
and ``len``. The order of the items in a set differs among the targets, so
the results must not depend on it.

The class ``Collection`` holds the sets in its properties, which the targets
serialize as sorted arrays. We pick the items so that a wrong order shows: the
strings outside the Basic Multilingual Plane sort differently by UTF-16 code
units than by code points, the integers differently as text than numerically,
and the literals of ``Direction`` differently by their names or by their
declaration than by their values.
"""
from enum import Enum
from typing import AbstractSet, Final, List, Optional, Sequence, Set

from icontract import DBC, invariant


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"
    Gamma = "gamma"


class Direction(Enum):
    North = "up"
    South = "down"
    East = "right"


@invariant(lambda self: len(self) > 0, "Code must not be empty.")
class Code(str):
    """Represent a non-empty code."""


Reserved_texts: Final[AbstractSet[str]] = constant_set(
    values=["reserved", "forbidden"],
    description="""List the texts which must not be used.""",
)

Lucky_numbers: Final[AbstractSet[int]] = constant_set(
    values=[7, 42],
    description="""List the numbers which bring luck.""",
)

Special_kinds: Final[AbstractSet[Kind]] = constant_set(
    values=[Kind.Beta, Kind.Gamma],
    description="""List the special kinds.""",
)


@verification
def texts_are_unique(texts: Sequence[str]) -> bool:
    """Check a local set of strings."""
    seen: Set[str] = set()
    for text in texts:
        if text in seen:
            return False

        seen.add(text)

    return True


@verification
def numbers_are_unique_between_zeros(numbers: Sequence[int]) -> bool:
    """Check a local set of integers which we reset at every zero."""
    seen: Set[int] = set()
    for number in numbers:
        if number == 0:
            seen = set()
            continue

        if number in seen:
            return False

        seen.add(number)

    return True


@verification
def kinds_are_unique(kinds: Sequence[Kind]) -> bool:
    """Check a local set of enumeration literals."""
    seen: Set[Kind] = set()
    for kind in kinds:
        if kind in seen:
            return False

        seen.add(kind)

    return True


@verification
def codes_are_unique(codes: Sequence[Code]) -> bool:
    """Check a local set of constrained primitives."""
    seen: Set[Code] = set()
    for code in codes:
        if code in seen:
            return False

        seen.add(code)

    return True


@verification
def flags_are_uniform(flags: Sequence[bool]) -> bool:
    """Check a local set of booleans queried with literals."""
    seen: Set[bool] = set()
    for flag in flags:
        seen.add(flag)

    return not (True in seen and False in seen)


@verification
def lengths_are_unique(texts: Sequence[str]) -> bool:
    """Check a local set of integers filled with and queried by lengths."""
    seen: Set[int] = set()
    for text in texts:
        if len(text) in seen:
            return False

        seen.add(len(text))

    return True


@verification
def add_texts(texts: Sequence[str], collected: Set[str]) -> bool:
    """Add :paramref:`texts` to :paramref:`collected`, a mutable set argument."""
    for text in texts:
        collected.add(text)

    return True


@verification
def is_in_texts(text: str, texts: AbstractSet[str]) -> bool:
    """Check whether :paramref:`text` is in :paramref:`texts`, a read-only set."""
    return text in texts


@verification
def is_in_optional_texts(text: str, texts: Optional[AbstractSet[str]]) -> bool:
    """Check whether :paramref:`text` is in :paramref:`texts`, if specified."""
    if texts is None:
        return False

    return text in texts


@verification
def is_in_kinds(kind: Kind, kinds: AbstractSet[Kind]) -> bool:
    """Check whether :paramref:`kind` is in :paramref:`kinds`, a read-only set."""
    return kind in kinds


@verification
def texts_are_disjoint(
    texts: Sequence[str], other_texts: Optional[Sequence[str]]
) -> bool:
    """
    Check that :paramref:`texts` and :paramref:`other_texts` share no text.

    We collect the texts into a local set through a mutable set argument, and
    pass the local sets, possibly optional, as read-only arguments.
    """
    seen: Set[str] = set()
    add_texts(texts, seen)

    others: Optional[Set[str]] = None
    if other_texts is not None:
        others = set()
        add_texts(other_texts, others)

    for text in texts:
        if is_in_optional_texts(text, others):
            return False

    if other_texts is not None:
        for other_text in other_texts:
            if is_in_texts(other_text, seen):
                return False

    return True


@verification
def text_is_not_reserved(text: str) -> bool:
    """Check a constant set passed as a read-only and as an optional argument."""
    return not is_in_texts(text, Reserved_texts) and not is_in_optional_texts(
        text, Reserved_texts
    )


@verification
def texts_are_all_short(texts: AbstractSet[str]) -> bool:
    """Check a for-loop over a read-only set argument."""
    for text in texts:
        if len(text) > 10:
            return False

    return True


@verification
def unique_texts_are_all_short(texts: Sequence[str]) -> bool:
    """Collect :paramref:`texts` into a local set, and check them all."""
    seen: Set[str] = set()
    add_texts(texts, seen)
    return texts_are_all_short(seen)


@verification
def numbers_are_all_small(numbers: Sequence[int]) -> bool:
    """Check ``all`` over a local set."""
    seen: Set[int] = set()
    for number in numbers:
        seen.add(number)

    return all(number < 1000 for number in seen)


@verification
def at_most_one_text_is_reserved(texts: Sequence[str]) -> bool:
    """Check the intersection of a constant set with a local set."""
    seen: Set[str] = set()
    add_texts(texts, seen)

    reserved = Reserved_texts.intersection(seen)
    return len(reserved) <= 1


@verification
def some_kind_is_not_special(
    kinds: Sequence[Kind], optional_kind: Optional[Kind]
) -> bool:
    """
    Check the difference of a local set and a constant set.

    We also add :paramref:`optional_kind`, if specified, to check adding
    a narrowed optional to a set.
    """
    seen: Set[Kind] = set()
    for kind in kinds:
        seen.add(kind)

    if optional_kind is not None:
        seen.add(optional_kind)

    return len(seen) == 0 or len(seen.difference(Special_kinds)) > 0


@invariant(
    lambda self: texts_are_unique(self.texts),
    "Texts must be unique.",
)
@invariant(
    lambda self: unique_texts_are_all_short(self.texts),
    "Texts must be at most 10 characters long.",
)
@invariant(
    lambda self: numbers_are_all_small(self.numbers),
    "Numbers must be smaller than 1000.",
)
@invariant(
    lambda self: at_most_one_text_is_reserved(self.texts),
    "At most one text must be reserved.",
)
@invariant(
    lambda self: some_kind_is_not_special(self.kinds, self.optional_kind),
    "Kinds and the optional kind, if any, must contain a kind which is not special.",
)
@invariant(
    lambda self: not (self.optional_kind is not None)
    or not (self.optional_kind in Special_kinds),
    "Optional kind must not be special.",
)
@invariant(
    lambda self: numbers_are_unique_between_zeros(self.numbers),
    "Numbers must be unique between the zeros.",
)
@invariant(
    lambda self: kinds_are_unique(self.kinds),
    "Kinds must be unique.",
)
@invariant(
    lambda self: codes_are_unique(self.codes),
    "Codes must be unique.",
)
@invariant(
    lambda self: flags_are_uniform(self.flags),
    "Flags must be either all true or all false.",
)
@invariant(
    lambda self: lengths_are_unique(self.texts),
    "Texts must be of unique lengths.",
)
@invariant(
    lambda self: text_is_not_reserved(self.text),
    "Text must not be reserved.",
)
@invariant(
    lambda self: not (self.number in Lucky_numbers),
    "Number must not be lucky.",
)
@invariant(
    lambda self: not (len(self.numbers) in Lucky_numbers),
    "Number of numbers must not be lucky.",
)
@invariant(
    lambda self: not is_in_kinds(self.kind, Special_kinds),
    "Kind must not be special.",
)
@invariant(
    lambda self: texts_are_disjoint(self.texts, self.optional_texts),
    "Optional texts must not share any text with texts.",
)
@invariant(
    lambda self: self.optional_texts_are_unique_ignoring(Reserved_texts),
    "Optional texts must be unique, apart from the reserved ones.",
)
class Something(DBC):
    text: str
    number: int
    kind: Kind
    texts: List[str]
    numbers: List[int]
    kinds: List[Kind]
    codes: List[Code]
    flags: List[bool]
    optional_texts: Optional[List[str]]
    optional_kind: Optional[Kind]

    @non_mutating
    def optional_texts_are_unique_ignoring(self, ignored: AbstractSet[str]) -> bool:
        """Check a local set in a method with a read-only set argument."""
        if self.optional_texts is None:
            return True

        seen: Set[str] = set()
        for text in self.optional_texts:
            if text in ignored:
                continue

            if text in seen:
                return False

            seen.add(text)

        return True

    def __init__(
        self,
        text: str,
        number: int,
        kind: Kind,
        texts: List[str],
        numbers: List[int],
        kinds: List[Kind],
        codes: List[Code],
        flags: List[bool],
        optional_texts: Optional[List[str]] = None,
        optional_kind: Optional[Kind] = None,
    ) -> None:
        self.text = text
        self.number = number
        self.kind = kind
        self.texts = texts
        self.numbers = numbers
        self.kinds = kinds
        self.codes = codes
        self.flags = flags
        self.optional_texts = optional_texts
        self.optional_kind = optional_kind


@invariant(
    lambda self: not is_in_texts("forbidden", self.texts),
    "Texts must not contain the forbidden text.",
)
@invariant(
    lambda self: len(self.numbers) <= 5,
    "There must be at most five numbers.",
)
@invariant(
    lambda self: all(number > -1000 for number in self.numbers),
    "Numbers must be greater than -1000.",
)
@invariant(
    lambda self: not (Direction.North in self.directions)
    or Direction.South in self.directions,
    "Directions must contain south if they contain north.",
)
@invariant(
    lambda self: not (self.optional_texts is not None)
    or len(self.optional_texts.intersection(self.texts)) == 0,
    "Optional texts must not share any text with texts.",
)
@invariant(
    lambda self: self.texts_are_not_all_in(Reserved_texts),
    "Texts must contain a text which is not reserved, if any.",
)
class Collection(DBC):
    texts: Set[str]
    numbers: Set[int]
    flags: Set[bool]
    directions: Set[Direction]
    codes: Set[Code]
    optional_texts: Optional[Set[str]]
    optional_directions: Optional[Set[Direction]]

    @non_mutating
    def texts_are_not_all_in(self, others: AbstractSet[str]) -> bool:
        """Check the difference of a set property and a set argument."""
        return len(self.texts) == 0 or len(self.texts.difference(others)) > 0

    def __init__(
        self,
        texts: Set[str],
        numbers: Set[int],
        flags: Set[bool],
        directions: Set[Direction],
        codes: Set[Code],
        optional_texts: Optional[Set[str]] = None,
        optional_directions: Optional[Set[Direction]] = None,
    ) -> None:
        self.texts = texts
        self.numbers = numbers
        self.flags = flags
        self.directions = directions
        self.codes = codes
        self.optional_texts = optional_texts
        self.optional_directions = optional_directions


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
