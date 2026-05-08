from typing import List

from icontract import invariant


# NOTE (mristin):
# The XSD generator expects the constrained primitive Value data type to be defined
# since we had to hard-wire it. If we remove that hard-wiring, we can also remove
# this definition as well.

class Value_data_type(str, DBC):
    pass


@invariant(lambda self: len(self) > 0, "Not empty")
class Name(str):
    pass


class Something:
    list_of_lists_of_names: List[List[Name]]

    def __init__(self, list_of_lists_of_names: List[List[Name]]) -> None:
        self.list_of_lists_of_names = list_of_lists_of_names


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
