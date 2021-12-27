class Something:
    @snapshot(lambda x, y: x + y > 0, name="0932invalid")
    def do_something(self, x: int, y: int) -> int:
        pass