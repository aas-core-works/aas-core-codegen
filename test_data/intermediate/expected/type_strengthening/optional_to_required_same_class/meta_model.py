class Something:
    pass


@abstract
class Abstract:
    some_property: Optional[Something]

    def __init__(self, some_property: Optional[Something]) -> None:
        self.some_property = some_property


class Concrete(Abstract):
    some_property: Something

    def __init__(self, some_property: Something) -> None:
        Abstract.__init__(self, some_property)


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
