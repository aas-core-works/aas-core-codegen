class Something:
    count: int

    @non_mutating
    def is_same_as(self, other: "Something") -> bool:
        return self.count == other.count

    @non_mutating
    def is_same_as_itself(self) -> bool:
        return self.is_same_as(self)

    def __init__(self, count: int) -> None:
        self.count = count


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
