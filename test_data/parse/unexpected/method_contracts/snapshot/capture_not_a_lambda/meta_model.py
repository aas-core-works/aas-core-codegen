class Something:
    @snapshot(capture=some_capture_function)
    def do_something(self, x: int) -> int:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
