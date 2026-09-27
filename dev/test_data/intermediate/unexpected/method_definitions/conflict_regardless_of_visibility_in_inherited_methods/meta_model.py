@abstract
class Parent:
    @implementation_specific
    @non_mutating
    def _describe(self) -> str:
        pass


class Child(Parent):
    @implementation_specific
    @non_mutating
    def describe(self) -> str:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
