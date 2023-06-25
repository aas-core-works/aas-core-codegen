class Something:
    @snapshot(lambda lst: lst.copy(), "lst")
    @ensure(lambda lst, OLD: lst == OLD.lst)
    def do_something(self, lst: List[int]) -> None:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
