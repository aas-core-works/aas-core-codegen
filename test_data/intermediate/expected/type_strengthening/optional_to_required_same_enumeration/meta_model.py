class SomeEnumeration(Enum):
    Good = "good"
    Better = "better"
    Best = "best"


@abstract
class Abstract:
    some_property: Optional[SomeEnumeration]

    def __init__(self, some_property: Optional[SomeEnumeration]) -> None:
        self.some_property = some_property


class Concrete(Abstract):
    some_property: SomeEnumeration

    def __init__(self, some_property: SomeEnumeration) -> None:
        Abstract.__init__(self, some_property)


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
