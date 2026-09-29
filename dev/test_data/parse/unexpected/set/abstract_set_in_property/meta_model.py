from typing import AbstractSet


class Something(DBC):
    texts: AbstractSet[str]

    def __init__(self, texts: AbstractSet[str]) -> None:
        self.texts = texts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
