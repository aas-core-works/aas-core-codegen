class SomeConcreteClass:
    """Represent something."""


class SomeContainerClass:
    x: List[SomeConcreteClass]

    def __init__(self, x: List[SomeConcreteClass]) -> None:
        self.x = x


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
