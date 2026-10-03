from typing import List, Optional


class Something(DBC):
    texts: List[List[Optional[str]]]

    def __init__(self, texts: List[List[Optional[str]]]) -> None:
        self.texts = texts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
