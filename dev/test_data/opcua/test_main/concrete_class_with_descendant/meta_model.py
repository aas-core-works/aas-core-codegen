@serialization(with_model_type=True)
class Something:
    some_str: str

    def __init__(self, some_str: str) -> None:
        self.some_str = some_str


class Something_more_concrete(Something):
    some_more_concrete_str: str

    def __init__(self, some_str: str, some_more_concrete_str: str) -> None:
        Something.__init__(self, some_str)

        self.some_more_concrete_str = some_more_concrete_str


class Container:
    something: Something

    def __init__(self, something: Something) -> None:
        self.something = something


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
