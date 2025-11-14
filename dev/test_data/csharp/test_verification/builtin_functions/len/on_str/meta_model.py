# fmt: off
@invariant(
    lambda self:
    len(self.some_property) >= 1,
    "Some property must be non-empty."
)
# fmt: on
class Something:
    some_property: str

    def __init__(self, some_property: str) -> None:
        self.some_property = some_property


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
