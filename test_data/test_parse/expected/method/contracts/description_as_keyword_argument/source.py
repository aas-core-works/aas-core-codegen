class Something:
    @require(
        lambda self, x: self.y < x,
        description="some contract")
    def do_something(self, x: int) -> int:
        pass