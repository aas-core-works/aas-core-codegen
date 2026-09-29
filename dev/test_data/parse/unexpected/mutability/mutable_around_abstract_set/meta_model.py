from typing import AbstractSet


@verification
def collect(texts: Mutable[AbstractSet[str]]) -> bool:
    return "x" in texts


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
