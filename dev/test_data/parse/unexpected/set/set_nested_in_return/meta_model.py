from typing import Set, Tuple


@verification
def texts_of(text: str) -> Tuple[Set[str], int]:
    result: Set[str] = set()
    result.add(text)
    return (result, 1)


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
