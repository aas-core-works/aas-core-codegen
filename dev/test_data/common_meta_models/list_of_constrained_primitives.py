"""
Check the lists of constrained primitives, their list literals and ``append``.

The list literal holds constrained primitives, while the appended items are
plain strings sliced from them.

We also check the membership ``in`` them. We look up a plain string in the list
of constrained primitives, a sliced string in a local list built with
``append``, and check for a sub-string in a constrained primitive.
"""
from typing import List, Sequence

from icontract import invariant


@invariant(lambda self: len(self) > 0, "Non-empty")
class Name(str):
    pass


@verification
def names_with(name: Name, names: Sequence[Name]) -> List[Name]:
    """Give :paramref:`name` followed by :paramref:`names`."""
    result = [name]
    for other in names:
        result.append(other)

    return result


@verification
def initials_of(names: Sequence[Name]) -> List[str]:
    """Give the first characters of :paramref:`names` in the same order."""
    initials: List[str] = []
    for name in names:
        initials.append(name[:1])

    return initials


@verification
def initials_are_unique(names: Sequence[Name]) -> bool:
    """Check that :paramref:`names` start with unique characters."""
    initials: List[str] = []
    for name in names:
        initial = name[:1]
        if initial in initials:
            return False

        initials.append(initial)

    return True


@verification
def is_in_names(text: str, names: Sequence[Name]) -> bool:
    """Check whether :paramref:`text` is in :paramref:`names`."""
    return text in names


@verification
def contains_space(name: Name) -> bool:
    """Check whether :paramref:`name` contains a space."""
    return " " in name


@invariant(
    lambda self: initials_are_unique(self.some_names),
    "Initials of some names must be unique.",
)
@invariant(
    lambda self: all(not contains_space(name) for name in self.some_names),
    "Some names must not contain spaces.",
)
@invariant(
    lambda self: not is_in_names("Mallory", self.some_names),
    "Some names must not contain Mallory.",
)
@invariant(
    lambda self: not ("Eve" in self.some_names),
    "Some names must not contain Eve.",
)
@invariant(
    lambda self: all(initial != "x" for initial in initials_of(self.some_names)),
    "Some names must not start with x.",
)
@invariant(
    lambda self: all(
        len(names_with(name, self.some_names)) == len(self.some_names) + 1
        for name in self.some_names
    ),
    "Each name followed by some names must be one longer than some names.",
)
class Something:
    some_names: List[Name]

    def __init__(self, some_names: List[Name]) -> None:
        self.some_names = some_names


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
