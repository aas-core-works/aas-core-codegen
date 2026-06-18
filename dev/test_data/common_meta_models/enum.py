from enum import Enum
from typing import List

from icontract import invariant


class Result(Enum):
    Ok = "ok"
    Not_ok = "not-ok"


class Something:
    some_result: Result

    def __init__(self, some_result: Result) -> None:
        self.some_result = some_result


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
