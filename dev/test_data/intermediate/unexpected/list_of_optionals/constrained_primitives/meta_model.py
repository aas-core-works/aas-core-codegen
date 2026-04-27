from typing import List, Optional

from icontract import invariant


@invariant(lambda self: self > 0, "Larger than zero")
class Positive(int):
    pass


class Something:
    maybe_positives: List[Optional[Positive]]

    def __init__(self, maybe_positives: List[Optional[Positive]]) -> None:
        self.maybe_positives = maybe_positives


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
