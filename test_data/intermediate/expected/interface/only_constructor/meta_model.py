# We explicitly test here that the constructor is not included in the signatures.
@abstract
class Abstract:
    x: int

    def __init__(self, x: int) -> None:
        self.x = x


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
