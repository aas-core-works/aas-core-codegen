from typing import List

from icontract import invariant


@invariant(lambda self: len(self) > 0, "Non-empty")
class Name(str):
    pass


class Something:
    some_names: List[Name]

    def __init__(self, some_names: List[Name]) -> None:
        self.some_names = some_names


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
