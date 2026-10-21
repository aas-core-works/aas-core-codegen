"""
Test the comparisons of booleans, integers, floats and lengths.

The meta-model follows the Python semantics, where ``False`` is smaller than
``True``. We test the ordering of strings in ``string_operations.py`` together
with the other operations on strings.
"""

from icontract import DBC, invariant


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
    lambda self: self.flag <= self.other_flag and len(self.text) < 1000,
    "Flag must imply the other flag and text must be shorter than 1000",
)
class Something(DBC):
    text: str
    flag: bool
    other_flag: bool
    count: int
    ratio: float

    def __init__(
        self,
        text: str,
        flag: bool,
        other_flag: bool,
        count: int,
        ratio: float,
    ) -> None:
        self.text = text
        self.flag = flag
        self.other_flag = other_flag
        self.count = count
        self.ratio = ratio


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
