"""
Test the comparisons of strings, booleans, integers, floats and lengths.

The meta-model follows the Python semantics, where the strings are ordered by
their characters (code points), and ``False`` is smaller than ``True``. Most other
languages order the strings by their UTF-16 code units, which differs from
the order of the characters beyond the Basic Multilingual Plane. Some of
the invariants are chosen such that the test data distinguishes the two orders.
"""

from icontract import DBC, invariant


@invariant(lambda self: len(self) > 0, "At least one character")
class Non_empty_string(str, DBC):
    pass


@verification
def text_is_between_bounds(text: str) -> bool:
    """Check the ordering of a string with the literals on both sides."""
    return "A" <= text and text < "z"


@verification
def name_is_not_after_text(name: Non_empty_string, text: str) -> bool:
    """Check the ordering of a constrained primitive with a string."""
    return not (name > text) and text >= name


@verification
def text_sorts_before_replacement_character(text: str) -> bool:
    """
    Check the ordering of a string with a character from U+E000 to U+FFFF.

    A character beyond the Basic Multilingual Plane such as "😀" (U+1F600) sorts
    after the replacement character (U+FFFD), but its UTF-16 code units (U+D83D and
    U+DE00) sort before it.
    """
    return text < "�"


@verification
def flags_are_ordered(flag: bool, other_flag: bool) -> bool:
    """Check all the ordering comparisons of booleans, where ``False < True``."""
    return (
        (flag < other_flag or flag == other_flag)
        and not (flag > other_flag)
        and other_flag >= flag
        and flag <= other_flag
        and flag >= False
    )


@verification
def count_is_in_range(count: int) -> bool:
    """Check the ordering comparisons of integers."""
    return 0 <= count and count < 100 and not (count > 99) and 99 >= count


@verification
def ratio_is_in_range(ratio: float) -> bool:
    """Check the ordering comparisons of floats."""
    return 0.0 <= ratio and ratio <= 1.0 and not (ratio > 1.0) and 0.0 < 1.0 + ratio


@verification
def text_fits_into_count(text: str, count: int) -> bool:
    """Check the ordering comparisons of lengths with integers."""
    return len(text) <= count and count >= len(text) and not (len(text) > 100)


@invariant(
    lambda self: text_is_between_bounds(self.name),
    "Name must be between A and z",
)
@invariant(
    lambda self: name_is_not_after_text(self.name, self.text),
    "Name must not sort after the text",
)
@invariant(
    lambda self: text_sorts_before_replacement_character(self.text),
    "Text must sort before the replacement character",
)
@invariant(
    lambda self: flags_are_ordered(self.flag, self.other_flag),
    "Flag implies the other flag",
)
@invariant(
    lambda self: count_is_in_range(self.count),
    "Count must be between 0 and 99",
)
@invariant(
    lambda self: ratio_is_in_range(self.ratio),
    "Ratio must be between 0 and 1",
)
@invariant(
    lambda self: text_fits_into_count(self.text, self.count),
    "Text must have at most count characters",
)
@invariant(
    lambda self: self.name < "zzz" and self.flag <= self.other_flag,
    "Name must sort before zzz and flag must imply the other flag",
)
class Something(DBC):
    text: str
    name: Non_empty_string
    flag: bool
    other_flag: bool
    count: int
    ratio: float

    def __init__(
        self,
        text: str,
        name: Non_empty_string,
        flag: bool,
        other_flag: bool,
        count: int,
        ratio: float,
    ) -> None:
        self.text = text
        self.name = name
        self.flag = flag
        self.other_flag = other_flag
        self.count = count
        self.ratio = ratio


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
