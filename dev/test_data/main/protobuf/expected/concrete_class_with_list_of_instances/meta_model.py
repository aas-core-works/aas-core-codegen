class Item:
    some_str: str

    def __init__(self, some_str: str) -> None:
        self.some_str = some_str


class Something:
    items: List[Item]
    optional_items: Optional[List[Item]]

    def __init__(
        self, items: List[Item], optional_items: Optional[List[Item]] = None
    ) -> None:
        self.items = items
        self.optional_items = optional_items


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
