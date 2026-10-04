from typing import Mapping


@verification
def some_count_is_zero(counts: Mapping[str, int]) -> bool:
    return any(count == 0 for text, count in counts.items())


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
