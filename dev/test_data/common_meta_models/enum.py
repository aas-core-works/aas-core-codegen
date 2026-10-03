from enum import Enum
from typing import List

from icontract import invariant


class Result(Enum):
    Ok = "ok"
    Not_ok = "not-ok"


@verification
def negated(result: Result) -> Result:
    """Negate :paramref:`result`, returning an enumeration literal."""
    if result == Result.Ok:
        return Result.Not_ok

    return Result.Ok


@invariant(
    lambda self: negated(negated(self.some_result)) == self.some_result,
    "Negating the result twice must give the result.",
)
class Something:
    some_result: Result

    def __init__(self, some_result: Result) -> None:
        self.some_result = some_result


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
