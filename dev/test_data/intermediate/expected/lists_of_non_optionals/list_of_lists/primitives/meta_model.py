from typing import List


class Something:
    list_of_lists_of_ints: List[List[int]]

    def __init__(self, list_of_lists_of_ints: List[List[int]]) -> None:
        self.list_of_lists_of_ints = list_of_lists_of_ints


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
