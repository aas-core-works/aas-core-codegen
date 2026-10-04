from typing import Mapping, Sequence


class Item(DBC):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


@verification
def some_func(counts: Sequence[Mapping[Item, int]]) -> bool:
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
