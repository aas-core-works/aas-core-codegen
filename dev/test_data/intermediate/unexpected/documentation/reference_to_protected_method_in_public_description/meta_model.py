@abstract
class Parent:
    @implementation_specific
    @non_mutating
    def _prefix(self) -> str:
        """Return the prefix."""

    @implementation_specific
    @non_mutating
    def describe(self) -> str:
        """Render the description starting with :meth:`_prefix`."""


class Child(Parent):
    pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
