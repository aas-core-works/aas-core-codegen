from typing import List


class List_of_primitives():
    strings: List[str]
    integers: List[int]
    booleans: List[bool]

    def __init__(self, strings: List[str], integers: List[int], booleans: List[bool]) -> None:
        self.strings = strings
        self.integers = integers
        self.booleans = booleans


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
