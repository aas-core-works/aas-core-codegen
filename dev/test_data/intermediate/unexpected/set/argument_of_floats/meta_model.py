from typing import AbstractSet


@verification
def is_known(number: float, numbers: AbstractSet[float]) -> bool:
    return number in numbers


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
