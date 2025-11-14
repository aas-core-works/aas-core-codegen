class Something:
    x: int

    @ensure(lambda self, result: self.x < result)
    def do_something(self, y: int) -> int:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
