class Something:
    @snapshot(lambda x, y: x + y > 0)
    def do_something(self, x: int, y: int) -> int:
        pass


__book_url__ = "dummy"
__book_version__ = "dummy"
