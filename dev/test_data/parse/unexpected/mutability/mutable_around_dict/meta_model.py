from typing import Dict


@verification
def forget(counts: Mutable[Dict[str, int]]) -> bool:
    counts.pop("a", None)
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
