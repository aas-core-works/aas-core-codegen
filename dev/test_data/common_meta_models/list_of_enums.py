"""Check the lists of enumeration literals, their list literals and ``append``."""
from enum import Enum
from typing import List, Sequence

from icontract import invariant


class Result(Enum):
    Ok = "ok"
    Fail = "fail"


@verification
def is_known(result: Result) -> bool:
    """Check whether :paramref:`result` is one of the known results."""
    for known in [Result.Ok, Result.Fail]:
        if known == result:
            return True

    return False


@verification
def failures_of(results: Sequence[Result]) -> List[Result]:
    """Give the failures among :paramref:`results`."""
    failures: List[Result] = []
    for result in results:
        if result == Result.Fail:
            failures.append(result)

    return failures


@invariant(
    lambda self: len(failures_of(self.some_results)) <= 1,
    "Some results must contain at most one failure.",
)
@invariant(
    lambda self: all(is_known(result) for result in self.some_results),
    "Some results must be known.",
)
class Something:
    some_results: List[Result]

    def __init__(self, some_results: List[Result]) -> None:
        self.some_results = some_results


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
