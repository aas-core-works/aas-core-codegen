# fmt: off
@invariant(
    lambda self:
    some_unexpected_builtin_function(self.some_property)
)
# fmt: on
class Something:
    some_property: str

    def __init__(self, some_property: str) -> None:
        self.some_property = some_property


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
