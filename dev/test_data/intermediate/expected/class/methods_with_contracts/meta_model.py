class Concrete:
    x: int

    @require(lambda x: x > 0)
    def __init__(self, x: int) -> None:
        self.x = x

    @require(lambda self: self.x > 2)
    @require(lambda number: number > 0)
    def some_func(self, number: int) -> int:
        """Do something."""


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
