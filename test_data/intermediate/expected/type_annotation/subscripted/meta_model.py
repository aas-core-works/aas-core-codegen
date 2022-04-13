class SomeConcreteClass:
    """Represent something."""


class SomeContainerClass:
    x: List[SomeConcreteClass]

    def __init__(self, x: List[SomeConcreteClass]) -> None:
        self.x = x


__book_url__ = "dummy"
__book_version__ = "dummy"
