class SomethingAbstract:
    property_a: str
    property_b: Optional[str]

    def __init__(
        self,
        property_a: str,
        # The default to None is missing here.
        property_b: Optional[str] = "abc",
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
