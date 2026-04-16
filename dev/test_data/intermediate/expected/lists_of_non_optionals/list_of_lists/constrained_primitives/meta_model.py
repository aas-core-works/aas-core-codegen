from typing import List

from icontract import invariant


@invariant(lambda self: self > 0, "Larger than zero")
class Positive(int):
    pass

class Something:
    list_of_lists_of_positives: List[List[Positive]]

    def __init__(self, list_of_lists_of_positives: List[List[Positive]]) -> None:
        self.list_of_lists_of_positives = list_of_list_of_positives

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
