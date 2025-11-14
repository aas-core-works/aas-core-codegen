class Something:
    @snapshot(lambda x, y: x + y > 0, name="0932invalid")
    def do_something(self, x: int, y: int) -> int:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
