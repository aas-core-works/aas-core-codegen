from enum import Enum
from typing import List

from icontract import invariant


# NOTE (mristin):
# The XSD generator expects the constrained primitive Value data type to be defined
# since we had to hard-wire it. If we remove that hard-wiring, we can also remove
# this definition as well.

class Value_data_type(str, DBC):
    pass


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


class Parentless_and_childless:
    identifier: str

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier


@invariant(
    lambda self: len(self.some_items) >= 2, "At least 2 elements"
)
@invariant(
    lambda self: len(self.list_of_parentless_and_childless) >= 3,
    "At least 3 elements"
)
class Something:
    some_items: List[Abstract_item]
    list_of_parentless_and_childless: List[Parentless_and_childless]

    def __init__(
            self,
            some_items: List[Abstract_item],
            list_of_parentless_and_childless: List[Parentless_and_childless]
    ) -> None:
        self.some_items = some_items
        self.list_of_parentless_and_childless = list_of_parentless_and_childless


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
