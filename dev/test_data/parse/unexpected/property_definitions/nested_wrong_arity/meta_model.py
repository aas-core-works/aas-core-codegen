from typing import List


class Something(DBC):
    texts: List[List[str, int]]

    def __init__(self, texts: List[List[str, int]]) -> None:
        self.texts = texts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
