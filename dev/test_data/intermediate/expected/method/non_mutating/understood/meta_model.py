class Something:
    def __init__(self) -> None:
        pass

    @non_mutating
    def get_something(self) -> int:
        return 4


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
