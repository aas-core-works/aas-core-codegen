"""
Provide the data shared by the generators of unit tests across the targets.

The generators of the unit tests for the individual SDKs live in the ``tests``
packages of the respective targets (*e.g.*, :py:mod:`aas_core_codegen.csharp.tests`).
Put here what these generators share so that all the SDKs are tested against
the same cases.
"""

from typing import Final, Sequence, Tuple

# region Arithmetic

# NOTE (mristin):
# Provide the cases for the generated unit tests of the arithmetic operations.
#
# The meta-model is written in Python, so the Python semantics of the modulo operator
# ``%`` and of the built-in ``abs`` hold for all the generated SDKs. However, the native
# operators and functions of the target languages behave differently in the corner
# cases. Most notably, Python floors the division so that the remainder takes the sign of
# the divisor (``-7 % 3 == 2``), while C#, C++, Go, Java and TypeScript truncate
# the division towards zero so that the remainder of their native ``%`` takes the sign
# of the dividend (``-7 % 3 == -1``).
#
# The generators hence transpile the modulo to helper functions (or library functions
# such as ``Math.floorMod`` in Java) which follow the Python semantics. We generate unit
# tests from the cases below for every SDK so that the clients can look up the behavior,
# and be certain about it.
#
# The expected values are computed by Python itself, so the cases can not diverge from
# the semantics of the meta-model.

#: Smallest 64-bit signed integer
INT64_MIN: Final[int] = -(2**63)

#: Largest 64-bit signed integer
INT64_MAX: Final[int] = 2**63 - 1

#: Largest integer which can be exactly represented as a double-precision
#: floating-point number, *e.g.*, as a ``number`` in TypeScript
MAX_SAFE_INTEGER: Final[int] = 2**53 - 1


class FloorModCase:
    """Represent a test case for the modulo."""

    #: The left operand
    dividend: Final[int]

    #: The right operand
    divisor: Final[int]

    #: The remainder according to the Python semantics
    expected: Final[int]

    #: Human-readable explanation of the case
    explanation: Final[str]

    def __init__(self, dividend: int, divisor: int, explanation: str) -> None:
        """Initialize with the given values and compute the expected remainder."""
        assert divisor != 0, "Division by zero is undefined; do not test it."
        self.dividend = dividend
        self.divisor = divisor
        self.expected = dividend % divisor
        self.explanation = explanation

    def is_safe_integer(self) -> bool:
        """Check that all the numbers are exactly representable as doubles."""
        return all(
            abs(number) <= MAX_SAFE_INTEGER
            for number in (self.dividend, self.divisor, self.expected)
        )


#: Cases for the modulo on 64-bit signed integers
FLOOR_MOD_CASES: Final[Sequence[FloorModCase]] = [
    FloorModCase(7, 3, "both operands positive"),
    FloorModCase(-7, 3, "the remainder takes the sign of the positive divisor"),
    FloorModCase(7, -3, "the remainder takes the sign of the negative divisor"),
    FloorModCase(-7, -3, "both operands negative"),
    FloorModCase(6, 3, "divisible, positive dividend"),
    FloorModCase(-6, 3, "divisible, negative dividend"),
    FloorModCase(6, -3, "divisible, negative divisor"),
    FloorModCase(0, 3, "zero dividend, positive divisor"),
    FloorModCase(0, -3, "zero dividend, negative divisor"),
    FloorModCase(2, 5, "dividend smaller than the positive divisor"),
    FloorModCase(-2, 5, "negative dividend smaller than the divisor"),
    FloorModCase(
        INT64_MAX, 2, "largest 64-bit integer, which is odd, by a positive divisor"
    ),
    FloorModCase(INT64_MAX, -2, "largest 64-bit integer by a negative divisor"),
    FloorModCase(INT64_MIN, 3, "smallest 64-bit integer by a positive divisor"),
    FloorModCase(
        INT64_MIN,
        -1,
        "smallest 64-bit integer by -1, which overflows with the native operator "
        "in some languages",
    ),
    FloorModCase(
        INT64_MIN,
        INT64_MAX,
        "smallest 64-bit integer by the largest one",
    ),
]

#: Cases for ``abs`` on 64-bit signed integers as ``(argument, expected)``.
#:
#: The absolute value of the smallest 64-bit integer overflows in all the languages
#: except Python, so we do not test it.
ABS_INT_CASES: Final[Sequence[Tuple[int, int]]] = [
    (5, 5),
    (-5, 5),
    (0, 0),
    (INT64_MAX, INT64_MAX),
    (-INT64_MAX, INT64_MAX),
]

#: Cases for ``abs`` on double-precision floating-point numbers as
#: ``(argument, expected)``
ABS_FLOAT_CASES: Final[Sequence[Tuple[float, float]]] = [
    (2.5, 2.5),
    (-2.5, 2.5),
    (0.0, 0.0),
    (-0.0, 0.0),
    (-1.7976931348623157e308, 1.7976931348623157e308),
]

for _case in FLOOR_MOD_CASES:
    assert (
        INT64_MIN <= _case.dividend <= INT64_MAX
        and INT64_MIN <= _case.divisor <= INT64_MAX
        and INT64_MIN <= _case.expected <= INT64_MAX
    ), f"Expected all the numbers to fit into 64-bit integers: {_case.__dict__}"

for _argument, _expected in ABS_INT_CASES:
    assert abs(_argument) == _expected
    assert INT64_MIN <= _argument <= INT64_MAX and _expected <= INT64_MAX

for _float_argument, _float_expected in ABS_FLOAT_CASES:
    assert abs(_float_argument) == _float_expected

# endregion
