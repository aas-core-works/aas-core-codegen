class Something:
    @snapshot(lambda z: z > 0)
    def do_something(self, x: int) -> int:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
