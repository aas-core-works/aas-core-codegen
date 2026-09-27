from typing import List


@verification
def fill(texts: Mutable[List[str]]) -> bool:
    texts[0] = "x"
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
