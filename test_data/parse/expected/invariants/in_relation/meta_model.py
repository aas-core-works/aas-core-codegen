Some_set: Set[str] = constant_set(values=["some literal", "another literal"])


@invariant(lambda self: self.some_property in Some_set)
class Something:
    some_property: str

    def __init__(self, some_property: str) -> None:
        self.some_property = some_property


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
