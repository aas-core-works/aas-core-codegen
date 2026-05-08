from typing import List

from icontract import DBC


class Something(DBC):
    some_bools: List[bool]
    some_ints: List[int]
    some_floats: List[float]
    some_strings: List[str]
    some_bytes: List[bytearray]

    def __init__(
            self,
            some_bools: List[bool],
            some_ints: List[int],
            some_floats: List[float],
            some_strings: List[str],
            some_bytes: List[bytearray]
    ) -> None:
        self.some_bools = some_bools
        self.some_ints = some_ints
        self.some_floats = some_floats
        self.some_strings = some_strings
        self.some_bytes = some_bytes


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
