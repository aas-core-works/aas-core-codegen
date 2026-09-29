from typing import Set


@verification
def collect(texts: Mutable[Set[str]]) -> bool:
    texts.add("x")
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
