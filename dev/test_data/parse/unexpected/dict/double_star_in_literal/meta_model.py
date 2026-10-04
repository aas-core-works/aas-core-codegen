from typing import Dict, Mapping


@verification
def some_func(counts: Mapping[str, int]) -> bool:
    other: Dict[str, int] = {"a": 1, **counts}
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
