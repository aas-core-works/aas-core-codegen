from typing import List, Optional


class Something:
    maybe_ints: List[Optional[int]]

    def __init__(self, maybe_ints: List[Optional[int]]) -> None:
        self.maybe_ints = maybe_ints


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
