class Something:
    @require(lambda self, x: self.y < x, description="some contract")
    def do_something(self, x: int) -> int:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
