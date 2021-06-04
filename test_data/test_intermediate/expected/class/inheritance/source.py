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


class Concrete(Abstract):
    yet_another_property: int

    @require(lambda yet_another_property: yet_another_property > 0)
    def __init__(
            self,
            some_property: int,
            another_property: int,
            yet_another_property: int
    ) -> None:
        Abstract.__init__(self, some_property, another_property)
        self.yet_another_property = yet_another_property

    def yet_another_func(self) -> None:
        pass
