Maximum_count: Final[int] = constant_int(value=10, description="Maximum count")


class Something:
    count: int

    @non_mutating
    def is_below_maximum(self) -> bool:
        return self.count < Maximum_count

    def __init__(self, count: int) -> None:
        self.count = count


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
