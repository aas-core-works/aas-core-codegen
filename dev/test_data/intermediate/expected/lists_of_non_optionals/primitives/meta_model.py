from typing import List


class Something:
    some_ints: List[int]

    def __init__(self, some_ints: List[int]) -> None:
        self.some_ints = some_ints


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
