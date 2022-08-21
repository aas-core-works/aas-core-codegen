@invariant(lambda self: re.match(r"^hello$", self.x), "X must match hello.")
class Something:
    x: str

    def __init__(self, x: str) -> None:
        self.x = x


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
