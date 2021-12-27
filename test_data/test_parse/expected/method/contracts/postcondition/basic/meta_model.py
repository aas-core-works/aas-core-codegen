class Something:
    @ensure(lambda self, result, x: self.y < x < result)
    def do_something(self, x: int) -> int:
        pass