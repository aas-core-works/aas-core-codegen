@invariant(lambda self: len(self) > 10, "Length more than 10 characters")
class SomeConstrainedPrimitive(str):
    pass


@abstract
class Abstract:
    some_property: Optional[SomeConstrainedPrimitive]

    def __init__(self, some_property: Optional[SomeConstrainedPrimitive]) -> None:
        self.some_property = some_property


class Concrete(Abstract):
    some_property: SomeConstrainedPrimitive

    def __init__(self, some_property: SomeConstrainedPrimitive) -> None:
        Abstract.__init__(self, some_property)


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
