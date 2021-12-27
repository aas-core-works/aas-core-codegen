# We explicitly test here that the parsed order of the contracts and snapshots is
# reversed w.r.t. the source code. This reversion is due to how Python applies
# decorators: from bottom up.


class Something:
    @require(lambda x: x > 0)
    @require(lambda y: y > 0)
    @snapshot(lambda x: x * 2, name="double_x")
    @snapshot(lambda y: y * 2, name="double_y")
    @ensure(lambda x, result: x > result)
    @ensure(lambda y, result: y > result)
    def do_something(self, x: int, y: int) -> int:
        pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
