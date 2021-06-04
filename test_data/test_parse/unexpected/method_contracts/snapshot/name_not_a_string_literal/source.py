class Something:
    @snapshot(lambda x, y: x + y > 0, name=SOME_CONSTANT)
    def do_something(self, x: int, y: int) -> int:
        pass