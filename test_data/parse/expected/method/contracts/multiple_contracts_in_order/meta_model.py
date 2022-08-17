# We explicitly test here that the parsed order of the contracts and snapshots is
# reversed w.r.t. the source code. This reversion is due to how Python applies
# decorators: from bottom up.


class Something:
    @require(lambda x: x > 0)
    @require(lambda y: y > 0)
    @snapshot(lambda x: x, name="double_x")
    @ensure(lambda x, result: x > result)
    @ensure(lambda y, result: y > result)
    def do_something(self, x: int, y: int) -> int:
        pass


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
