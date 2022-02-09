class Something:
    @require(lambda self, x: self.y < x, "some contract")
    def do_something(self, x: int) -> int:
        pass


__book_url__ = "dummy"
__book_version__ = "dummy"
