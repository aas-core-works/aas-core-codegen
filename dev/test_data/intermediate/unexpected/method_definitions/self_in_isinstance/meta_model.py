@abstract
class Something:
    count: int

    @non_mutating
    def is_specific(self) -> bool:
        return isinstance(self, Specific)

    def __init__(self, count: int) -> None:
        self.count = count


class Specific(Something):
    def __init__(self, count: int) -> None:
        Something.__init__(self, count)


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
