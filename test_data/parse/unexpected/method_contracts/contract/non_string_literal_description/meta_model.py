class Something:
    @require(lambda x: x > 0, description=3)
    def do_something(self, x: int) -> int:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
