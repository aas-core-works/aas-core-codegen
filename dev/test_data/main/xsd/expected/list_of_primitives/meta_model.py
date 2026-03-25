from typing import List

from icontract import DBC

# NOTE (mristin):
# The XSD generator expects the constrained primitive Value data type to be defined
# since we had to hard-wire it. If we remove that hard-wiring, we can also remove
# this definition as well.

class Value_data_type(str, DBC):
    pass


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
