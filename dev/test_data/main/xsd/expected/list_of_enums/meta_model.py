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
    some_results: List[Result]

    def __init__(self, some_results: List[Result]) -> None:
        self.some_results = some_results


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
