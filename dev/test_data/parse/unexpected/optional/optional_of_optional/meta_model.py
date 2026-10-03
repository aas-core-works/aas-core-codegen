from typing import Optional


class Something(DBC):
    text: Optional[Optional[str]]

    def __init__(self, text: Optional[Optional[str]] = None) -> None:
        self.text = text


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
