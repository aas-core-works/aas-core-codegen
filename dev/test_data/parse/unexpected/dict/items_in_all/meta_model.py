from typing import Mapping


@verification
def all_counts_are_positive(counts: Mapping[str, int]) -> bool:
    return all(count > 0 for text, count in counts.items())


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
