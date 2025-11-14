class Item:
    pass


# fmt: off
@invariant(
    lambda self:
    len(self.some_property) >= 1,
    "Some property must contain at least one item."
)
# fmt: on
class Something:
    some_property: List[Item]

    def __init__(self, some_property: List[Item]) -> None:
        self.some_property = some_property


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
