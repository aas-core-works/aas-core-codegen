from typing import List, Sequence


class Something(DBC):
    texts: List[Sequence[str]]

    def __init__(self, texts: List[Sequence[str]]) -> None:
        self.texts = texts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
