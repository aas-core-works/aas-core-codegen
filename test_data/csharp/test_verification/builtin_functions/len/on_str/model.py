# fmt: off
@invariant(
    lambda self:
    len(self.some_property) > 0
)
# fmt: on
class Something:
    some_property: str

    def __init__(self, some_property: str) -> None:
        self.some_property = some_property


__book_url__ = "dummy"
__book_version__ = "dummy"
