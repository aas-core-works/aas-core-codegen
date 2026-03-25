from typing import List

from icontract import DBC, invariant


# NOTE (mristin):
# These invariants are probably not translatable to JSON schema due to limitations
# of infer_for_schema, but they should still be silently ignored, without raising
# an error.
@invariant(lambda self: len(self.some_bytes[0]) > 0, "Invariant 9")
@invariant(lambda self: self.some_strings[0] == "ok", "Invariant 8")
@invariant(lambda self: self.some_floats[0] == 1.0, "Invariant 7")
@invariant(lambda self: self.some_ints[0] == 1, "Invariant 6")
@invariant(lambda self: self.some_bools[0] == True, "Invariant 5")
# NOTE (mristin):
# The following invariants should be handled by infer_for_schema, and thus reflected
# in the JSON schema.
@invariant(lambda self: len(self.some_bools) > 0, "Invariant 4")
@invariant(lambda self: len(self.some_ints) > 0, "Invariant 3")
@invariant(lambda self: len(self.some_floats) > 0, "Invariant 2")
@invariant(lambda self: len(self.some_strings) > 0, "Invariant 1")
@invariant(lambda self: len(self.some_bytes) > 0, "Invariant 0")
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
