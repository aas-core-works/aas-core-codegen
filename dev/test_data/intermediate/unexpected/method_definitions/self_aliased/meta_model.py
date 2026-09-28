class Something:
    count: int

    @non_mutating
    def aliased_count(self) -> int:
        alias = self
        return alias.count

    def __init__(self, count: int) -> None:
        self.count = count


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
