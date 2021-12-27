class Something:
    x: int

    @ensure(lambda self, result: self.x < result)
    def do_something(self, y: int) -> int:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
