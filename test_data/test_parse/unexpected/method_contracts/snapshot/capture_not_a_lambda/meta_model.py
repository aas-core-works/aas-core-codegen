class Something:
    @snapshot(capture=some_capture_function)
    def do_something(self, x: int) -> int:
        pass
