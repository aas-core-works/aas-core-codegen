from enum import Enum
from typing import List

from icontract import invariant


# NOTE (mristin):
# The XSD generator expects the constrained primitive Value data type to be defined
# since we had to hard-wire it. If we remove that hard-wiring, we can also remove
# this definition as well.

class Value_data_type(str, DBC):
    pass


class Result(Enum):
    Ok = "ok"
    Fail = "fail"


class Something:
    list_of_lists_of_results: List[List[Result]]

    def __init__(self, list_of_lists_of_results: List[List[Result]]) -> None:
        self.list_of_lists_of_results = list_of_lists_of_results


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
