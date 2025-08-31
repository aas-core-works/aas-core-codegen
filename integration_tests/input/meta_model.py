from typing import List


class My_Class:
    string_prop: str
    int_prop: int
    bool_prop: bool

    def __init__(self, string_prop: str, int_prop: int, bool_prop: bool) -> None:
        self.string_prop = string_prop
        self.int_prop = int_prop
        self.bool_prop = bool_prop


class Root:
    foo: My_Class
    foos: List[My_Class]
    strings: List[str]
    integers: List[int]
    booleans: List[bool]

    def __init__(
        self,
        foo: My_Class,
        foos: List[My_Class],
        strings: List[str],
        integers: List[int],
        booleans: List[bool],
    ) -> None:
        self.foo = foo
        self.foos = foos
        self.strings = strings
        self.integers = integers
        self.booleans = booleans


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
