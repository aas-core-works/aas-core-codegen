from typing import Dict, Mapping


@verification
def some_func(counts: Mapping[str, Dict[str, int]]) -> bool:
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
