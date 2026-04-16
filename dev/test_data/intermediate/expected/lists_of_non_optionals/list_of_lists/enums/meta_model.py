from enum import Enum
from typing import List

from icontract import invariant


class Result(Enum):
    Ok = "ok"
    Fail = "fail"


class Something:
    list_of_lists_of_results: List[List[Result]]

    def __init__(self, list_of_lists_of_results: List[List[Result]]) -> None:
        self.list_of_lists_of_results = list_of_lists_of_results


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
