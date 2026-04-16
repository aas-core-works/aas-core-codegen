from typing import List, Optional

from icontract import invariant


class Item:
    pass


class Something:
    maybe_items: List[Optional[Item]]

    def __init__(self, maybe_items: List[Optional[Item]]) -> None:
        self.maybe_items = maybe_items


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
