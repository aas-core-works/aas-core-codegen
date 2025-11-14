Some_set: Set[str] = constant_set(values=["some literal", "another literal"])


@invariant(
    lambda self: self.some_property in Some_set,
    "Some property must belong to Some set.",
)
class Something:
    some_property: str

    def __init__(self, some_property: str) -> None:
        self.some_property = some_property


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
