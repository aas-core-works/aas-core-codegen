class Something:
    def do_something(
        self, x: int = 1984, y: int = 2021, z: Optional[int] = None
    ) -> None:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
