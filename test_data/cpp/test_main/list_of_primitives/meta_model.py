from typing import List


class My_class:
    pass


class List_of_primitives:
    strings: List[str]
    integers: List[int]
    booleans: List[bool]
    classes: List[My_class]

    def __init__(
        self,
        strings: List[str],
        integers: List[int],
        booleans: List[bool],
        classes: List[My_class],
    ) -> None:
        self.strings = strings
        self.integers = integers
        self.booleans = booleans
        self.classes = classes


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
