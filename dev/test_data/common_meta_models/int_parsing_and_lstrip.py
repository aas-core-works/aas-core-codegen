"""
Check parsing the integers from the strings with ``int`` and ``str.lstrip``.

The transpiled ``int`` accepts only an optional sign followed by the ASCII digits,
and only the safe integers, *i.e.*, the integers within -(2^53 - 1) and 2^53 - 1.
Otherwise, it throws. Hence, the meta-model checks the text before it calls ``int``.
"""
from typing import Optional

from icontract import DBC, invariant


@verification
def matches_decimal(text: str) -> bool:
    """Check that :paramref:`text` is an optional sign followed by ASCII digits."""
    pattern = "^[-+]?[0-9]+$"
    return match(pattern, text) is not None


@verification
def is_safe_integer(text: str) -> bool:
    """
    Check that :paramref:`text` is a decimal integer within the safe range.

    The safe integers have at most 16 significant digits. We compare the digits
    piece-wise so that ``int`` is never given a number out of the safe range.
    """
    digits = text.lstrip("+-").lstrip("0")

    return matches_decimal(text) and (
        len(digits) < 16
        or (
            len(digits) == 16
            and (
                int(digits[:15]) < 900719925474099
                or (int(digits[:15]) == 900719925474099 and int(digits[15:]) <= 1)
            )
        )
    )


@verification
def is_xs_long(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid ``xs:long``, *i.e.*, a 64-bit integer.

    The 64-bit integers exceed the safe range of ``int``, so we parse the 19
    significant digits in two pieces of at most 10 digits. The smallest
    ``xs:long`` is -2^63, so the bound of the negative values is one larger.
    """
    if not matches_decimal(text):
        return False

    digits = text.lstrip("+-").lstrip("0")
    if len(digits) < 19:
        return True

    if len(digits) > 19:
        return False

    head = int(digits[:10])
    tail = int(digits[10:])

    if text[:1] == "-":
        return head < 9223372036 or (head == 9223372036 and tail <= 854775808)

    return head < 9223372036 or (head == 9223372036 and tail <= 854775807)


@verification
def parse_number(text: str) -> int:
    """
    Check returning the parsed integer from a verification function.

    The caller has to check that :paramref:`text` is a safe integer.
    """
    return int(text)


@invariant(lambda self: matches_decimal(self), "Decimal must be a decimal integer")
class Decimal_text(str, DBC):
    pass


@invariant(lambda self: is_xs_long(self.long_text), "Long text must be an xs:long")
@invariant(
    lambda self: not (self.maybe_number is not None)
    or is_safe_integer(self.maybe_number),
    "Maybe number must be a safe integer",
)
@invariant(
    lambda self: not is_safe_integer(self.decimal) or int(self.decimal) != 13,
    "Decimal must not be 13",
)
@invariant(lambda self: is_safe_integer(self.decimal), "Decimal must be a safe integer")
@invariant(
    lambda self: len(self.padded.lstrip("0")) <= 3,
    "Padded must have at most three significant digits",
)
@invariant(
    lambda self: self.padded.lstrip("0") != "",
    "Padded must not consist only of zeros",
)
@invariant(
    lambda self: not is_safe_integer(self.number) or parse_number(self.number) <= 1000,
    "Number must be at most 1000",
)
@invariant(
    lambda self: not is_safe_integer(self.number) or int(self.number) >= -1000,
    "Number must be at least -1000",
)
@invariant(lambda self: is_safe_integer(self.number), "Number must be a safe integer")
class Something(DBC):
    number: str
    padded: str
    decimal: Decimal_text
    long_text: str
    maybe_number: Optional[str]

    def __init__(
        self,
        number: str,
        padded: str,
        decimal: Decimal_text,
        long_text: str,
        maybe_number: Optional[str] = None,
    ) -> None:
        self.number = number
        self.padded = padded
        self.decimal = decimal
        self.long_text = long_text
        self.maybe_number = maybe_number


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
