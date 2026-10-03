from typing import List, Set


class Something(DBC):
    numbers: List[Set[float]]

    def __init__(self, numbers: List[Set[float]]) -> None:
        self.numbers = numbers


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
