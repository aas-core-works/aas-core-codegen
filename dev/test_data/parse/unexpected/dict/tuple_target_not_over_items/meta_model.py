from typing import Mapping


@verification
def some_func(counts: Mapping[str, int]) -> bool:
    for text, count in counts:
        pass

    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
