from typing import Sequence


class Something:
    texts: Sequence[str]

    def __init__(self, texts: Sequence[str]) -> None:
        self.texts = texts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
