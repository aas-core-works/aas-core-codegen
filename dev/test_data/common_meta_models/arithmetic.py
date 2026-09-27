"""
Test the modulo, the arithmetic negation and ``abs``.

The meta-model follows the Python semantics, where the remainder of the modulo takes
the sign of the divisor (``-4 % 7 == 3``). The native modulo in most other languages
takes the sign of the dividend (``-4 % 7 == -4``). Some of the invariants are chosen
such that the test data distinguishes the two semantics.
"""

from typing import Optional

from icontract import DBC, invariant


@invariant(lambda self: self % 2 == 0, "Even")
class Even_int(int, DBC):
    pass


@verification
def has_small_remainder(number: int) -> bool:
    """
    Check that the remainder of the division by 7 is smaller than 3.

    The remainder is stored in a local variable on purpose. For example, -4 has
    the remainder 3 in Python, but -4 with the native modulo in many other languages.
    """
    remainder = number % 7
    return remainder < 3


@verification
def is_within_distance(number: int, center: int, distance: int) -> bool:
    """Check that the ``number`` is at most ``distance`` away from ``center``."""
    return abs(number - center) <= distance


@verification
def is_negative(number: int) -> bool:
    """Check that the number is negative, negating it twice."""
    return -number > 0 and -(-number) < 0


@verification
def is_length_aligned(text: str, alignment: int) -> bool:
    """
    Check that the length of the text is a multiple of the alignment.

    This is the modulo of a length by an integer which is not a literal.
    """
    return len(text) % alignment == 0


@verification
def has_remainder_one_by_length(number: int, text: str) -> bool:
    """
    Check that the number gives the remainder 1 when divided by the length plus one.

    This is the modulo of an integer which is not a literal by a length.
    """
    return number % (len(text) + 1) == 1


@invariant(
    lambda self: not (self.optional_ratio is not None)
    or (-self.optional_ratio < 0.5 and abs(self.optional_ratio) < 2.0),
    "Optional ratio must be larger than -0.5 and smaller than 2 in absolute terms",
)
@invariant(
    lambda self: not (self.optional_number is not None)
    or (self.optional_number % 5 == 4 and abs(self.optional_number) < 100),
    "Optional number must give the remainder 4 when divided by 5, and "
    "be smaller than 100 in absolute terms",
)
@invariant(
    lambda self: has_remainder_one_by_length(self.alignment, self.text),
    "Alignment must give the remainder 1 when divided by the length of text plus one",
)
@invariant(
    lambda self: is_length_aligned(self.text, self.alignment),
    "Text must be aligned",
)
@invariant(lambda self: -self.ratio <= 1.0, "Ratio must be at least -1")
@invariant(
    lambda self: abs(self.ratio) <= 1.5, "Ratio must be at most 1.5 in absolute terms"
)
@invariant(
    lambda self: is_within_distance(self.deviation, 0, 10),
    "Deviation must be at most 10 in absolute terms",
)
@invariant(lambda self: is_negative(self.negative), "Negative must be negative")
@invariant(lambda self: len(self.text) % 2 == 0, "Text must have an even length")
@invariant(
    lambda self: self.by_negative % -3 == -1,
    "By negative must give the remainder -1 when divided by -3",
)
@invariant(
    lambda self: has_small_remainder(self.small),
    "Small must give a remainder smaller than 3 when divided by 7",
)
@invariant(
    lambda self: self.offset % 7 == 3,
    "Offset must give the remainder 3 when divided by 7",
)
class Something(DBC):
    even: Even_int
    offset: int
    small: int
    by_negative: int
    text: str
    negative: int
    deviation: int
    ratio: float
    alignment: int
    optional_number: Optional[int]
    optional_ratio: Optional[float]

    def __init__(
        self,
        even: Even_int,
        offset: int,
        small: int,
        by_negative: int,
        text: str,
        negative: int,
        deviation: int,
        ratio: float,
        alignment: int,
        optional_number: Optional[int] = None,
        optional_ratio: Optional[float] = None,
    ) -> None:
        self.even = even
        self.offset = offset
        self.small = small
        self.by_negative = by_negative
        self.text = text
        self.negative = negative
        self.deviation = deviation
        self.ratio = ratio
        self.alignment = alignment
        self.optional_number = optional_number
        self.optional_ratio = optional_ratio


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
