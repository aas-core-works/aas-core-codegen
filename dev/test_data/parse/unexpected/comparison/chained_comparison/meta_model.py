@invariant(
    lambda self: "A" <= self.text < "z",
    "Some description.",
)
class Something(DBC):
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
