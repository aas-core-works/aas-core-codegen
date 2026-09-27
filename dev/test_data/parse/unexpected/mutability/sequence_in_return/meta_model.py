from typing import Sequence


class Something:
    text: str

    def __init__(self, text: str) -> None:
        self.text = text

    @implementation_specific
    @non_mutating
    def texts(self) -> Sequence[str]:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
