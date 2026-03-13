@abstract
class Something_abstract:
    some_str: str

    def __init__(self, some_str: str) -> None:
        self.some_str = some_str


@abstract
class Another_abstract:
    another_str: str

    def __init__(self, another_str: str) -> None:
        self.another_str = another_str


class Concrete(Something_abstract, Another_abstract):
    def __init__(self, some_str: str, another_str: str) -> None:
        Something_abstract.__init__(self, some_str)
        Another_abstract.__init__(self, another_str)


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
