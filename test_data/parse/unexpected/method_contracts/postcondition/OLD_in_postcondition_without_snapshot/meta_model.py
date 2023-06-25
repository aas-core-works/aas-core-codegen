class Something:
    @ensure(lambda OLD: len(OLD.lst) > 0)
    def do_something(self, x: int, y: int) -> int:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
