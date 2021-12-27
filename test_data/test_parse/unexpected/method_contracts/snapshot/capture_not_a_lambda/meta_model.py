class Something:
    @snapshot(capture=some_capture_function)
    def do_something(self, x: int) -> int:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
