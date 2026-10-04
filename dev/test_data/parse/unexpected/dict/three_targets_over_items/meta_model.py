from typing import Mapping


@verification
def some_func(counts: Mapping[str, int]) -> bool:
    for text, count, other in counts.items():
        pass

    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
