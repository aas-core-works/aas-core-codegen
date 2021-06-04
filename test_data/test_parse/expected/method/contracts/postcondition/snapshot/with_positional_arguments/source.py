class Something:
    @snapshot(lambda lst: lst[:], "lst")
    @ensure(lambda lst, OLD: lst == OLD.lst)
    def do_something(self, lst: List[int]) -> None:
        pass