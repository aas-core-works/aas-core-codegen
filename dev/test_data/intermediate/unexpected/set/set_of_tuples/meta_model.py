from typing import Set, Tuple


class Something(DBC):
    pairs: Set[Tuple[str, int]]

    def __init__(self, pairs: Set[Tuple[str, int]]) -> None:
        self.pairs = pairs


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
