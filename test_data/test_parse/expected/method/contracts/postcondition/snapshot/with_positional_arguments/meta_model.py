class Something:
    @snapshot(lambda lst: lst[:], "lst")
    @ensure(lambda lst, OLD: lst == OLD.lst)
    def do_something(self, lst: List[int]) -> None:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
