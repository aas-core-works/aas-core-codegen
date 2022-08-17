@abstract
class VeryAbstract:
    some_property: int

    @require(lambda some_property: some_property > 0)
    def __init__(self, some_property: int) -> None:
        self.some_property = some_property

    def some_func(self) -> None:
        pass


@abstract
class Abstract(VeryAbstract):
    another_property: int

    @require(lambda another_property: another_property > 0)
    def __init__(self, some_property: int, another_property: int) -> None:
        VeryAbstract.__init__(self, some_property)
        self.another_property = another_property

    def another_func(self) -> None:
        pass


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
