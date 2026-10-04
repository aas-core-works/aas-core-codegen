from typing import Mapping


@verification
def forget(counts: Mutable[Mapping[str, int]]) -> bool:
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
