class Concrete:
    x: int

    def __init__(self, x: int) -> None:
        self.x = x


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
