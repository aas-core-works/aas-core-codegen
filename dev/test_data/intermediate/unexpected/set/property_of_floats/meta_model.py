from typing import Set


class Something(DBC):
    numbers: Set[float]

    def __init__(self, numbers: Set[float]) -> None:
        self.numbers = numbers


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
