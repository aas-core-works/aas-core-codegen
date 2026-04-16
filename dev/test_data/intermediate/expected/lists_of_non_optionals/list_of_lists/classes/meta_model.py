from enum import Enum
from typing import List

from icontract import invariant


@abstract
@serialization(with_model_type=True)
class AbstractItem:
    pass

class SomeItem(AbstractItem):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

class AnotherItem(AbstractItem):
    serial_number: int

    def __init__(self, serial_number: int) -> None:
        self.serial_number = serial_number

class Something:
    list_of_lists_of_items: List[List[AbstractItem]]

    def __init__(self, list_of_lists_of_items: List[List[AbstractItem]]) -> None:
        self.list_of_lists_of_items = list_of_lists_of_items

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
