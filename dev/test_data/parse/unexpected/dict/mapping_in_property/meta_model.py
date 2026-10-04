from typing import Mapping


class Something(DBC):
    counts: Mapping[str, int]

    def __init__(self, counts: Mapping[str, int]) -> None:
        self.counts = counts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
