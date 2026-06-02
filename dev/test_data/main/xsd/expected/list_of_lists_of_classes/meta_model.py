from enum import Enum
from typing import List

from icontract import invariant


@abstract
@serialization(with_model_type=True)
class Abstract_item:
    pass


class Some_item(Abstract_item):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class Another_item(Abstract_item):
    serial_number: int

    def __init__(self, serial_number: int) -> None:
        self.serial_number = serial_number


class Something:
    list_of_lists_of_items: List[List[Abstract_item]]

    def __init__(self, list_of_lists_of_items: List[List[Abstract_item]]) -> None:
        self.list_of_lists_of_items = list_of_lists_of_items


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
