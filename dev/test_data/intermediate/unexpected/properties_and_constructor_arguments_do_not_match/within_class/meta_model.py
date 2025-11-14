class Something:
    property_a: str
    property_b: str

    property_c: Optional[str]
    property_d: Optional[str]

    def __init__(
        self,
        property_b: str,
        property_a: str,
        property_d: Optional[str] = None,
        property_c: Optional[str] = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        self.property_d = property_d


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
