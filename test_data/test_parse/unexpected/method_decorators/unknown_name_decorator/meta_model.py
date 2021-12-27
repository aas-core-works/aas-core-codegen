class Something:
    @unknown_decorator
    def __init__(self) -> None:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
