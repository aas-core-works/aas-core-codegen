# The invariants are contradicting.
@invariant(lambda self: len(self.some_prop) == 10)
@invariant(lambda self: len(self.some_prop) == 11)
class Something:
    some_prop: str

    def __init__(self, some_prop: str) -> None:
        self.some_prop = some_prop


__book_version__ = "dummy"
__book_url__ = "dummy"
__xml_namespace__ = "https://dummy.com"
