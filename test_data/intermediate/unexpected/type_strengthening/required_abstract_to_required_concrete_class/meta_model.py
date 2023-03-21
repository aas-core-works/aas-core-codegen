@abstract
@serialization(with_model_type=True)
class SomeAbstract:
    pass


class SomeConcrete(SomeAbstract):
    pass


@abstract
class Abstract:
    some_property: SomeAbstract

    def __init__(self, some_property: SomeAbstract) -> None:
        self.some_property = some_property


class Concrete(Abstract):
    some_property: SomeConcrete

    def __init__(self, some_property: SomeConcrete) -> None:
        Abstract.__init__(self, some_property)


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
