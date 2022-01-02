@abstract
class Abstract:
    some_property: int

    @require(lambda some_property: some_property > 0)
    def __init__(self, some_property: int) -> None:
        self.some_property = some_property

    def some_func(self) -> None:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
