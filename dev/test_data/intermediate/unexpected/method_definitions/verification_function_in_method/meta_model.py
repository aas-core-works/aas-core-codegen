@verification
def is_positive(number: int) -> bool:
    return number > 0


class Something:
    count: int

    @non_mutating
    def has_positive_count(self) -> bool:
        return is_positive(self.count)

    def __init__(self, count: int) -> None:
        self.count = count


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
