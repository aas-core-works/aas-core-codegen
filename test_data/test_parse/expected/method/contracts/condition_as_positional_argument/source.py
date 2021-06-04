class Something:
    @require(
        lambda self, x: self.y < x)
    def do_something(self, x: int) -> int:
        pass
