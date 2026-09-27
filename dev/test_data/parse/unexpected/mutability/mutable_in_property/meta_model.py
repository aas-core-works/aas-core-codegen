class Item:
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


class Something:
    item: Mutable["Item"]

    def __init__(self, item: Item) -> None:
        self.item = item


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
