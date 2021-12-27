class Something:
    @unknown_lib.do_something(lambda x: x > 0)
    def __init__(self) -> None:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
