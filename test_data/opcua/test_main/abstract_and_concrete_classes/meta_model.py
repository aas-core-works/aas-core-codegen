@abstract
@serialization(with_model_type=True)
class Something_abstract:
    some_str: str

    def __init__(self, some_str: str) -> None:
        self.some_str = some_str


class Something_concrete(Something_abstract):
    something_str: str

    def __init__(self, some_str: str, something_str: str) -> None:
        Something_abstract.__init__(self, some_str)

        self.something_str = something_str


class Another_concrete(Something_abstract):
    another_str: str

    def __init__(self, some_str: str, another_str: str) -> None:
        Something_abstract.__init__(self, some_str)

        self.another_str = another_str


class Container:
    something_abstract: Something_abstract

    def __init__(self, something_abstract: Something_abstract) -> None:
        self.something_abstract = something_abstract


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
