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
    some_items: List[Abstract_item]

    def __init__(self, some_items: List[Abstract_item]) -> None:
        self.some_items = some_items


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
