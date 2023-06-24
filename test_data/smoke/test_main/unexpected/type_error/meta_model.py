class Value:
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


# ERROR: ``len(.)`` on a class is not defined.
@invariant(lambda self: len(self.value) > 1, "Value longer than 1")
class Something:
    value: Value

    def __init__(self, value: Value) -> None:
        self.value = value


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
