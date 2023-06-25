@invariant(lambda self: re.match(r"^hello$", self.x), "X must match hello.")
class Something:
    x: str

    def __init__(self, x: str) -> None:
        self.x = x


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
