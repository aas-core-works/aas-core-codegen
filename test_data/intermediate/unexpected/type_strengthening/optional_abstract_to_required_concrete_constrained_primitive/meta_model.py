@invariant(lambda self: len(self) > 3, "Length more than 3")
class SomeAbstractConstrainedPrimitive(str):
    pass


@invariant(lambda self: len(self) > 10, "Length more than 10")
class SomeConcreteConstrainedPrimitive(SomeAbstractConstrainedPrimitive):
    pass


@abstract
class Abstract:
    some_property: Optional[SomeAbstractConstrainedPrimitive]

    def __init__(
        self, some_property: Optional[SomeAbstractConstrainedPrimitive]
    ) -> None:
        self.some_property = some_property


class Concrete(Abstract):
    some_property: SomeConcreteConstrainedPrimitive

    def __init__(self, some_property: SomeConcreteConstrainedPrimitive) -> None:
        Abstract.__init__(self, some_property)


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
