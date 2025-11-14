@invariant(lambda self: len(self) > 2, "At least 3 characters")
class Something_constrained(str):
    pass


@invariant(lambda self: len(self) < 10, "At most 9 characters.")
class More_constrained(str):
    pass


class Container:
    more_constrained: More_constrained

    def __init__(self, more_constrained: More_constrained) -> None:
        self.more_constrained = more_constrained


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
