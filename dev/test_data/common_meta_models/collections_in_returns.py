"""
Check the transpilation of the lists, the sets and the tuples as return values.

We return the local sets, the copies of the lists, the results of the calls, and
the tuple literals of them, possibly optional, both from the verification
functions and from the methods. The callers use the returned sets as
the containers of ``in``, as the collections of the for-loops, and as
the arguments of ``len``.

The class ``Something`` holds no sets itself, and its method takes no sets,
so that the interfaces of the targets need to import the sets for the return
values alone.
"""
from enum import Enum
from typing import List, Optional, Sequence, Set, Tuple

from icontract import DBC, invariant


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"
    Gamma = "gamma"


@verification
def unique_texts_of(texts: Sequence[str]) -> Set[str]:
    """Return a local set of strings."""
    result: Set[str] = set()
    for text in texts:
        result.add(text)

    return result


@verification
def unique_kinds_of(kinds: Sequence[Kind]) -> Set[Kind]:
    """Return a local set of enumeration literals."""
    result: Set[Kind] = set()
    for kind in kinds:
        result.add(kind)

    return result


@verification
def optional_unique_texts_of(texts: Optional[Sequence[str]]) -> Optional[Set[str]]:
    """Return either ``None`` or the result of a call as an optional set."""
    if texts is None:
        return None

    return unique_texts_of(texts)


@verification
def copy_of_texts(texts: Sequence[str]) -> List[str]:
    """Return a copy of a list."""
    return list(texts)


@verification
def unique_texts_and_duplicates_of(texts: Sequence[str]) -> Tuple[Set[str], int]:
    """Return a tuple literal of a local set and an integer, possibly a literal."""
    seen: Set[str] = set()
    duplicates: int = 0
    for text in texts:
        if text in seen:
            duplicates = duplicates + 1

        seen.add(text)

    if duplicates == 0:
        return (seen, 0)

    return (seen, duplicates)


@verification
def copy_and_unique_texts_of(texts: Sequence[str]) -> Tuple[List[str], Set[str]]:
    """Return a tuple literal of a copied list and the result of a call."""
    return (list(texts), unique_texts_of(texts))


@verification
def unique_texts_twice_of(texts: Sequence[str]) -> Tuple[Set[str], Set[str]]:
    """
    Return the same local set twice in a tuple literal.

    C++ moves a local set into a returned tuple literal, but must not move a set
    which occurs twice, as the second item would be moved-from and empty.
    """
    seen: Set[str] = set()
    for text in texts:
        seen.add(text)

    return (seen, seen)


@verification
def texts_are_unique(texts: Sequence[str]) -> bool:
    """Check the items of a returned tuple holding a set."""
    unique_and_duplicates = unique_texts_and_duplicates_of(texts)
    return unique_and_duplicates[1] == 0 and len(unique_and_duplicates[0]) == len(texts)


@verification
def copied_texts_are_unique(texts: Sequence[str]) -> bool:
    """Check a returned copy of a list against a returned set."""
    copy_and_unique = copy_and_unique_texts_of(texts)
    return len(copy_and_unique[0]) == len(copy_and_unique[1])


@verification
def optional_texts_are_unique(texts: Optional[Sequence[str]]) -> bool:
    """Assign a returned optional set to a local variable, and check it."""
    if texts is None:
        return True

    unique = optional_unique_texts_of(texts)
    return unique is not None and len(unique) == len(texts)


@verification
def no_kind_is_gamma(kinds: Sequence[Kind]) -> bool:
    """Loop over a returned set."""
    for kind in unique_kinds_of(kinds):
        if kind == Kind.Gamma:
            return False

    return True


@invariant(
    lambda self: texts_are_unique(self.texts),
    "Texts must be unique.",
)
@invariant(
    lambda self: copied_texts_are_unique(self.texts),
    "Texts must be unique, checked on a copy.",
)
@invariant(
    lambda self: len(unique_texts_twice_of(self.texts)[0])
    == len(unique_texts_twice_of(self.texts)[1]),
    "Unique texts must be returned twice the same.",
)
@invariant(
    lambda self: len(copy_of_texts(self.texts)) <= 3,
    "There must be at most three texts.",
)
@invariant(
    lambda self: optional_texts_are_unique(self.optional_texts),
    "Optional texts must be unique.",
)
@invariant(
    lambda self: no_kind_is_gamma(self.kinds),
    "Kinds must not contain gamma.",
)
@invariant(
    lambda self: len(self.kinds) == 0 or Kind.Alpha in self.unique_kinds(),
    "Kinds must contain alpha, if specified.",
)
class Something(DBC):
    texts: List[str]
    kinds: List[Kind]
    optional_texts: Optional[List[str]]

    @non_mutating
    def unique_kinds(self) -> Set[Kind]:
        """Return a local set from a method."""
        result: Set[Kind] = set()
        for kind in self.kinds:
            result.add(kind)

        return result

    def __init__(
        self,
        texts: List[str],
        kinds: List[Kind],
        optional_texts: Optional[List[str]] = None,
    ) -> None:
        self.texts = texts
        self.kinds = kinds
        self.optional_texts = optional_texts


@invariant(
    lambda self: all(len(group) > 0 for group in self.groups),
    "Groups must not be empty.",
)
class Grouped(DBC):
    """
    Hold a list of sets so that a set is the variable of ``all``.

    C++ binds the variable of ``all`` in a lambda by a constant reference, so it
    needs to know that a set is referencable.
    """

    groups: List[Set[str]]

    def __init__(self, groups: List[Set[str]]) -> None:
        self.groups = groups


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
