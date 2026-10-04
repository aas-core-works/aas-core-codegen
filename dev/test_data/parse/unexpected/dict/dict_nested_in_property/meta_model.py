from typing import Dict, List, Optional


class Something(DBC):
    counts: Optional[List[Dict[str, int]]]

    def __init__(self, counts: Optional[List[Dict[str, int]]] = None) -> None:
        self.counts = counts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
