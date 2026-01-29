@invariant(lambda self: len(self) > 0, "Non-empty")
class Something(str):
    pass


@invariant(lambda self: len(self) <= 9, "At most 9 characters")
class Child(Something):
    pass


@invariant(lambda self: len(self) <= 5, "At most 5 characters")
class Grand_child(Child):
    pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
