@invariant(
    lambda self: len(self.name) > 2, "Constraint 1: Name with at least 3 characters"
)
class Something_concrete:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


@invariant(
    lambda self: len(self.name) < 10, "Constraint 2: Name with at most 9 characters."
)
class Something_more_concrete(Something_concrete):
    def __init__(self, name: str) -> None:
        Something_concrete.__init__(self, name)


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
