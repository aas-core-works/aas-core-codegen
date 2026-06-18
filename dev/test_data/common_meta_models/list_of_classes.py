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


# NOTE (mristin):
# This class does not inherit from any other class nor does it have any descendants.
# This allows us to test the edge case where a class does not require a model type for
# serialization.
class Simple:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class Something:
    some_items: List[Abstract_item]
    some_simples: List[Simple]

    def __init__(
        self, some_items: List[Abstract_item], some_simples: List[Simple]
    ) -> None:
        self.some_items = some_items
        self.some_simples = some_simples


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
