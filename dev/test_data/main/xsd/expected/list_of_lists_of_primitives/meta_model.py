from typing import List


# NOTE (mristin):
# The XSD generator expects the constrained primitive Value data type to be defined
# since we had to hard-wire it. If we remove that hard-wiring, we can also remove
# this definition as well.

class Value_data_type(str, DBC):
    pass


class Something:
    list_of_lists_of_ints: List[List[int]]

    def __init__(self, list_of_lists_of_ints: List[List[int]]) -> None:
        self.list_of_lists_of_ints = list_of_lists_of_ints


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
