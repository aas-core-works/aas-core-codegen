from typing import Sequence


@verification
def fill(texts: Mutable[Sequence[str]]) -> bool:
    texts[0] = "x"
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
