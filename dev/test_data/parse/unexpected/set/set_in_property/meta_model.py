from typing import Set


class Something(DBC):
    texts: Set[str]

    def __init__(self, texts: Set[str]) -> None:
        self.texts = texts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
