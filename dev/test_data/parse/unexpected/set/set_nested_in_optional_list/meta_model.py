from typing import List, Optional, Set


class Something(DBC):
    texts: Optional[List[Set[str]]]

    def __init__(self, texts: Optional[List[Set[str]]] = None) -> None:
        self.texts = texts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
