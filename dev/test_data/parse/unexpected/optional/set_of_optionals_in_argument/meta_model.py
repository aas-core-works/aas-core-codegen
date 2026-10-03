from typing import AbstractSet, Optional


class Something(DBC):
    text: str

    @non_mutating
    def is_known(self, texts: AbstractSet[Optional[str]]) -> bool:
        return True

    def __init__(self, text: str) -> None:
        self.text = text


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
