@serialization(with_model_type=True)
class Something:
    some_str: str

    def __init__(self, some_str: str) -> None:
        self.some_str = some_str


class More_concrete(Something):
    another_str: str

    def __init__(self, some_str: str, another_str: str) -> None:
        Something.__init__(self, some_str)
        self.another_str = another_str


class Container:
    something: Something
    list_of_somethings: List[Something]

    def __init__(
        self, something: Something, list_of_somethings: List[Something]
    ) -> None:
        self.something = something
        self.list_of_somethings = list_of_somethings


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
