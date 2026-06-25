from enum import Enum
from typing import List

from icontract import invariant


class Result(Enum):
    Ok = "ok"
    Fail = "fail"


class Something:
    some_results: List[Result]

    def __init__(self, some_results: List[Result]) -> None:
        self.some_results = some_results


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
