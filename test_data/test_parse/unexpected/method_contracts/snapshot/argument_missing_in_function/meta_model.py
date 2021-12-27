class Something:
    @snapshot(lambda z: z > 0)
    def do_something(self, x: int) -> int:
        pass
