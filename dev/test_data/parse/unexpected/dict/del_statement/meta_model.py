from typing import Dict


@verification
def forget(counts: Dict[str, int]) -> bool:
    del counts["a"]
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
