from typing import List


class Item:
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


@verification
def rename_all(items: List[Mutable["Item"]]) -> bool:
    for item in items:
        item.text = "x"

    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
