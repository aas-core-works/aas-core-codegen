from enum import Enum
from typing import AbstractSet, Final


class Some_enum(Enum):
    First = "first"
    Second = "second"
    Third = "third"


SOME_BOOL: Final[bool] = constant_bool(value=True, description="A boolean constant.")

SOME_INT: Final[int] = constant_int(value=42, description="An integer constant.")

SOME_FLOAT: Final[float] = constant_float(value=3.14, description="A float constant.")

SOME_STRING: Final[str] = constant_str(
    value="some string", description="A string constant."
)

SOME_SET_OF_INTS: Final[AbstractSet[int]] = constant_set(
    values=[1, 2, 3],
    description="A set of integer constants.",
)

SOME_SET_OF_STRINGS: Final[AbstractSet[str]] = constant_set(
    values=["first value", "second value"],
    description="A set of string constants.",
)

SOME_SET_OF_ENUM_LITERALS: Final[AbstractSet[Some_enum]] = constant_set(
    values=[Some_enum.First, Some_enum.Second],
    description="A set of enumeration literals.",
)


class Something:
    some_enum: Some_enum

    def __init__(self, some_enum: Some_enum) -> None:
        self.some_enum = some_enum


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
