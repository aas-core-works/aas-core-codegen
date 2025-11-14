class Something:
    some_property: Optional[str]

    def __init__(self, some_property: Optional[str] = None) -> None:
        self.some_property = some_property


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
