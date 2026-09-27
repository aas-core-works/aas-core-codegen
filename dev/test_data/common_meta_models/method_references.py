from icontract import DBC, invariant


# NOTE (mristin):
# The reference in the description of a verification function lives outside
# the types module in most targets.
@verification
def is_described(text: str) -> bool:
    """
    Check that :paramref:`text` is not empty.

    This is meant to check the result of :meth:`Item.describe`.
    """
    return len(text) > 0


# NOTE (mristin):
# The unqualified reference is resolved in the context of the class.
@abstract
@serialization(with_model_type=True)
class Item(DBC):
    """
    Represent an item.

    See :meth:`describe` for a human-readable description.
    """

    label: str

    @implementation_specific
    @non_mutating
    def describe(self) -> str:
        """Render a human-readable description of the item."""
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return "Item " + self.label

    def __init__(self, label: str) -> None:
        self.label = label


# NOTE (mristin):
# The qualified references refer both to an abstract and a concrete class.
@invariant(lambda self: self.size > 0, "The size must be positive.")
class Box(Item):
    """
    Represent a box.

    Its :meth:`Item.describe` is complemented by :meth:`Box.volume`.
    """

    size: int

    @implementation_specific
    @non_mutating
    def volume(self) -> int:
        """
        Compute the volume of the box.

        The unqualified reference to the inherited :meth:`describe` is resolved in
        the context of the class.
        """
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return self.size * self.size * self.size

    def __init__(self, label: str, size: int) -> None:
        Item.__init__(self, label)
        self.size = size


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
