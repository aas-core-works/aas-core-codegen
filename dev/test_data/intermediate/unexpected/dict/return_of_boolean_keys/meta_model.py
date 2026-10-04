from typing import Dict, Sequence


@verification
def some_func(texts: Sequence[str]) -> Dict[bool, int]:
    result: Dict[bool, int] = {}
    return result


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
