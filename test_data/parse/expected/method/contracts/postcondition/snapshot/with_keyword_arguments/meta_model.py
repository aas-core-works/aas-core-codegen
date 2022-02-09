class Something:
    @snapshot(capture=lambda lst: lst.copy(), name="lst")
    @ensure(lambda lst, OLD: lst == OLD.lst)
    def do_something(self, lst: List[int]) -> None:
        pass


__book_url__ = "dummy"
__book_version__ = "dummy"
