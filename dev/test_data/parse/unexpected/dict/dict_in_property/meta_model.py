from typing import Dict


class Something(DBC):
    counts: Dict[str, int]

    def __init__(self, counts: Dict[str, int]) -> None:
        self.counts = counts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
