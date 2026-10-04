"""
Check the transpilation of the dictionaries.

We check the local dictionaries created with ``dict()``, ``{}`` and dictionary
literals, the keys of strings, integers, constrained primitives and enumeration
literals, the look-ups with ``in``, ``[...]``, ``get`` with and without a default,
the setting of the items, the removal with ``pop``, ``len``, and the iteration over
the keys and over the items, also in ``any`` and ``all``.

We pass the dictionaries as read-only (``Mapping``) and as mutable (``Dict``)
arguments, also as optional arguments, and return them from the verification
functions. We also nest the dictionaries in the lists and in the other
dictionaries.

The order of the iteration over a dictionary differs among the targets, so
the results must not depend on it.

The invariants of ``Something`` call the verification functions with
the dictionaries built from its list properties.

The class ``Registry`` holds the dictionaries in its properties, which the targets
serialize with the keys sorted. We pick the keys so that a wrong order shows: the
strings outside the Basic Multilingual Plane sort differently by UTF-16 code
units than by code points, the integers differently as text than numerically, and
the literals of ``Direction`` differently by their names or by their
declaration than by their values. We
also nest the dictionaries in the lists, hold the instances and the constrained
primitives as keys and as values, and check them in the invariants.
"""
from enum import Enum
from typing import Dict, Final, List, Mapping, Optional, Sequence

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


class Item(DBC):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


@verification
def count_texts(texts: Sequence[str]) -> Dict[str, int]:
    """Count the :paramref:`texts` in a new dictionary."""
    counts: Dict[str, int] = {}
    for text in texts:
        counts[text] = counts.get(text, 0) + 1

    return counts


@verification
def count_texts_into(texts: Sequence[str], counts: Dict[str, int]) -> bool:
    """Count the :paramref:`texts` in a mutable dictionary argument."""
    for text in texts:
        if text in counts:
            counts[text] = counts[text] + 1
        else:
            counts[text] = 1

    return True


@verification
def texts_are_unique(texts: Sequence[str]) -> bool:
    """Check the iteration over the items of a returned dictionary."""
    counts = count_texts(texts)
    for text, count in counts.items():
        if count > 1:
            return False

    return True


@verification
def kinds_are_unique(kinds: Sequence[Kind]) -> bool:
    """Check a local dictionary of enumeration literals created with ``dict()``."""
    first_index_by_kind: Dict[Kind, int] = dict()
    for i in range(0, len(kinds)):
        if kinds[i] in first_index_by_kind:
            return False

        first_index_by_kind[kinds[i]] = i

    return True


@verification
def codes_are_unique(codes: Sequence[Code]) -> bool:
    """Check ``get`` without a default on the keys of constrained primitives."""
    seen_by_code: Dict[Code, bool] = {}
    for code in codes:
        seen: Optional[bool] = seen_by_code.get(code)
        if seen is not None:
            return False

        seen_by_code[code] = True

    return True


@verification
def weight_of_kinds(kinds: Sequence[Kind]) -> int:
    """Sum up the weights of the :paramref:`kinds` from a read-only literal."""
    weight_by_kind: Final[Mapping[Kind, int]] = {
        Kind.Alpha: 1,
        Kind.Beta: 2,
        Kind.Gamma: 3,
    }

    result = 0
    for kind in kinds:
        result = result + weight_by_kind[kind]

    return result


@verification
def numbers_are_named(numbers: Sequence[int]) -> bool:
    """Check a literal of integer keys, including a negative one."""
    name_by_number: Final[Mapping[int, str]] = {1: "one", -1: "minus one", 0: "zero"}
    return all(number in name_by_number for number in numbers)


@verification
def count_numbers(numbers: Sequence[int], counts: Dict[int, int]) -> bool:
    """Count the :paramref:`numbers` in a mutable dictionary argument."""
    for number in numbers:
        counts[number] = counts.get(number, 0) + 1

    return True


@verification
def forget_zeros(counts: Dict[int, int]) -> bool:
    """Remove the zeros from a mutable dictionary argument."""
    counts.pop(0, None)
    return True


@verification
def all_counts_are_small(counts: Mapping[int, int]) -> bool:
    """Check ``all`` over the keys of a read-only dictionary argument."""
    return all(counts[number] < 3 for number in counts)


@verification
def some_count_is_one(counts: Mapping[int, int]) -> bool:
    """Check ``any`` over the keys of a read-only dictionary argument."""
    return any(counts[number] == 1 for number in counts)


@verification
def non_zero_numbers_are_rare(numbers: Sequence[int]) -> bool:
    """
    Check that every number but zero repeats at most twice.

    We pass a local dictionary to a mutable and then to read-only arguments.
    """
    counts: Dict[int, int] = {}
    count_numbers(numbers, counts)
    forget_zeros(counts)

    return len(counts) == 0 or (
        all_counts_are_small(counts) and some_count_is_one(counts)
    )


@verification
def is_counted(text: str, counts: Optional[Mapping[str, int]]) -> bool:
    """Check ``in`` on an optional read-only dictionary argument."""
    if counts is None:
        return False

    return text in counts


@verification
def texts_are_disjoint(
    texts: Sequence[str], other_texts: Optional[Sequence[str]]
) -> bool:
    """Check an optional local dictionary passed as an optional argument."""
    others: Optional[Dict[str, int]] = None
    if other_texts is not None:
        others = {}
        count_texts_into(other_texts, others)

    for text in texts:
        if is_counted(text, others):
            return False

    return True


@verification
def texts_are_grouped_by_length(texts: Sequence[str]) -> bool:
    """Check a dictionary nested in a dictionary, and the loops over them."""
    groups: Dict[int, Dict[str, bool]] = {}
    for text in texts:
        if not (len(text) in groups):
            groups[len(text)] = {}

        groups[len(text)][text] = True

    for length, group in groups.items():
        for text in group:
            if len(text) != length:
                return False

    return len(groups) <= len(texts)


@verification
def item_names_match_keys(items_by_name: Mapping[str, Item]) -> bool:
    """Check the values of instances in a read-only dictionary argument."""
    for name in items_by_name:
        if items_by_name[name].name != name:
            return False

    for name, item in items_by_name.items():
        if item.name != name:
            return False

    return True


@verification
def nested_labels_are_short(
    labels: Mapping[str, Sequence[Sequence[Mapping[int, str]]]]
) -> bool:
    """Check the dictionaries nested in the lists nested in a dictionary."""
    for key in labels:
        if (
            len(labels[key]) > 0
            and len(labels[key][0]) > 0
            and 1 in labels[key][0][0]
            and len(labels[key][0][0][1]) > 10
        ):
            return False

    for key, rows in labels.items():
        for row in rows:
            for label_by_number in row:
                for number, label in label_by_number.items():
                    if len(label) > number + 10:
                        return False

    return True


@invariant(
    lambda self: texts_are_unique(self.texts),
    "Texts must be unique.",
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
    lambda self: weight_of_kinds(self.kinds) <= 5,
    "Kinds must weigh at most 5.",
)
@invariant(
    lambda self: numbers_are_named(self.numbers),
    "Numbers must be named.",
)
@invariant(
    lambda self: non_zero_numbers_are_rare(self.numbers),
    "Numbers but zero must repeat at most twice, and some must not repeat.",
)
@invariant(
    lambda self: texts_are_disjoint(self.texts, self.optional_texts),
    "Optional texts must not share any text with texts.",
)
@invariant(
    lambda self: texts_are_grouped_by_length(self.texts),
    "Texts must be grouped by their lengths.",
)
@invariant(
    lambda self: self.counts_are_at_least(1, count_texts(self.texts)),
    "Texts must be counted at least once.",
)
class Something(DBC):
    texts: List[str]
    numbers: List[int]
    kinds: List[Kind]
    codes: List[Code]
    items: List[Item]
    optional_texts: Optional[List[str]]

    @non_mutating
    def counts_are_at_least(self, minimum: int, counts: Mapping[str, int]) -> bool:
        """Check a read-only dictionary argument in a method."""
        for text in self.texts:
            if counts.get(text, 0) < minimum:
                return False

        return True

    def __init__(
        self,
        texts: List[str],
        numbers: List[int],
        kinds: List[Kind],
        codes: List[Code],
        items: List[Item],
        optional_texts: Optional[List[str]] = None,
    ) -> None:
        self.texts = texts
        self.numbers = numbers
        self.kinds = kinds
        self.codes = codes
        self.items = items
        self.optional_texts = optional_texts


@invariant(
    lambda self: all_counts_are_small(self.counts_by_number),
    "Counts by number must be smaller than 3.",
)
@invariant(
    lambda self: len(self.counts_by_number) <= 5,
    "There must be at most five counts by number.",
)
@invariant(
    lambda self: item_names_match_keys(self.items_by_name),
    "Items must be named by their keys.",
)
@invariant(
    lambda self: nested_labels_are_short(self.labels),
    "Labels must be short.",
)
@invariant(
    lambda self: all(
        self.kinds_by_code[code] != Kind.Gamma for code in self.kinds_by_code
    ),
    "Kinds by code must not be gamma.",
)
@invariant(
    lambda self: all(len(self.codes_by_name[name]) <= 5 for name in self.codes_by_name),
    "Codes by name must be at most 5 characters long.",
)
@invariant(
    lambda self: not (self.optional_counts is not None)
    or len(self.optional_counts) > 0,
    "Optional counts must not be empty, if specified.",
)
@invariant(
    lambda self: self.weight_is_at_most(10),
    "Weights must sum up to at most 10.",
)
class Registry(DBC):
    counts: Dict[str, int]
    counts_by_number: Dict[int, int]
    weights: Dict[Direction, int]
    kinds_by_code: Dict[Code, Kind]
    codes_by_name: Dict[str, Code]
    items_by_name: Dict[str, Item]
    labels: Dict[str, List[List[Dict[int, str]]]]
    optional_counts: Optional[Dict[str, int]]

    @non_mutating
    def weight_is_at_most(self, maximum: int) -> bool:
        """Check the iteration over the items of a dictionary property."""
        total = 0
        for direction, weight in self.weights.items():
            total = total + weight

        return total <= maximum

    def __init__(
        self,
        counts: Dict[str, int],
        counts_by_number: Dict[int, int],
        weights: Dict[Direction, int],
        kinds_by_code: Dict[Code, Kind],
        codes_by_name: Dict[str, Code],
        items_by_name: Dict[str, Item],
        labels: Dict[str, List[List[Dict[int, str]]]],
        optional_counts: Optional[Dict[str, int]] = None,
    ) -> None:
        self.counts = counts
        self.counts_by_number = counts_by_number
        self.weights = weights
        self.kinds_by_code = kinds_by_code
        self.codes_by_name = codes_by_name
        self.items_by_name = items_by_name
        self.labels = labels
        self.optional_counts = optional_counts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
