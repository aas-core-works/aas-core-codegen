from typing import List, Optional

from icontract import DBC, invariant


@invariant(lambda self: self, "Always true")
class ConstrainedBool(bool, DBC):
    pass


@invariant(lambda self: self > 0, "Larger than zero")
class PositiveInt(int, DBC):
    pass


@invariant(lambda self: self > 0.0, "Larger than zero")
class PositiveFloat(float, DBC):
    pass


@invariant(lambda self: len(self) > 0, "At least one character")
class NonEmptyString(str, DBC):
    pass


@invariant(lambda self: len(self) > 0, "At least one byte")
class NonEmptyBytes(bytearray, DBC):
    pass


class Something(DBC):
    some_bool: ConstrainedBool
    some_int: PositiveInt
    some_float: PositiveFloat
    some_string: NonEmptyString
    some_bytes: NonEmptyBytes

    def __init__(
        self,
        some_bool: ConstrainedBool,
        some_int: PositiveInt,
        some_float: PositiveFloat,
        some_string: NonEmptyString,
        some_bytes: NonEmptyBytes,
    ) -> None:
        self.some_bool = some_bool
        self.some_int = some_int
        self.some_float = some_float
        self.some_string = some_string
        self.some_bytes = some_bytes


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
