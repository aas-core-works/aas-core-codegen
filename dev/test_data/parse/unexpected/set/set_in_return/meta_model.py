from typing import Set


@verification
def texts_of(text: str) -> Set[str]:
    result: Set[str] = set()
    result.add(text)
    return result


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
