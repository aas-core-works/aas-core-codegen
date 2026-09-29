class Something:
    number: int

    def __init__(self, number: int) -> None:
        self.number = number


@verification
def some_func(something: Mutable[Something]) -> bool:
    something.number: int = 0
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
