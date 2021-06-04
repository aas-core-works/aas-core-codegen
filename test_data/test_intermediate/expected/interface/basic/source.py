@abstract
class Abstract:
    some_property: int

    @require(lambda some_property: some_property > 0)
    def __init__(self, some_property: int) -> None:
        self.some_property = some_property

    def some_func(self) -> None:
        pass
