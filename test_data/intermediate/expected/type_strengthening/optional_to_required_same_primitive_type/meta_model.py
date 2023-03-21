class Abstract:
    some_property: Optional[str]

    def __init__(self, some_property: Optional[str]) -> None:
        self.some_property = some_property


class Concrete(Abstract):
    some_property: str

    def __init__(self, some_property: str) -> None:
        Abstract.__init__(self, some_property)


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
