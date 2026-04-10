from typing import List, Optional

from icontract import DBC, invariant


class Something(DBC):
    some_bool: bool
    some_int: int
    some_float: float
    some_string: str
    some_bytes: bytearray

    def __init__(
            self,
            some_bool: bool,
            some_int: int,
            some_float: float,
            some_string: str,
            some_bytes: bytearray,
    ) -> None:
        self.some_bool = some_bool
        self.some_int = some_int
        self.some_float = some_float
        self.some_string = some_string
        self.some_bytes = some_bytes


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
