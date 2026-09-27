from icontract import DBC, invariant


# region Verification functions


# NOTE (mristin):
# The leading underscore signals an internal function, *i.e.*, the function is
# visible only within the generated SDK, but not to its users.


@verification
def _matches_digits(text: str) -> bool:
    """Check that :paramref:`text` consists only of digits."""
    pattern = "^[0-9]+$"
    return match(pattern, text) is not None


@verification
def _is_short(text: str) -> bool:
    """
    Check that :paramref:`text` is at most 8 characters long.

    It complements :func:`_matches_digits`.
    """
    return len(text) <= 8


@verification
@implementation_specific
def _is_palindrome(text: str) -> bool:
    """Check that :paramref:`text` reads the same backwards."""
    # NOTE (mristin):
    # This implementation will not be transpiled, but is given here as reference.
    return text == text[::-1]


# NOTE (mristin):
# The public function calls the internal functions.
@verification
def is_short_number(text: str) -> bool:
    """Check that :paramref:`text` is a short number."""
    return _matches_digits(text) and _is_short(text)


# endregion


# NOTE (mristin):
# The invariants call both the public and the internal functions.
@invariant(lambda self: is_short_number(self.number), "The number must be short.")
@invariant(lambda self: _is_palindrome(self.code), "The code must be a palindrome.")
@abstract
@serialization(with_model_type=True)
class Item(DBC):
    number: str
    code: str

    # NOTE (mristin):
    # The leading underscore signals a protected method. It is not part of
    # the interface, and serves only as a helper to the implementation-specific
    # methods, here in the concrete descendants.
    @implementation_specific
    @non_mutating
    def _prefix(self) -> str:
        """Return the prefix of the description."""
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return "Item"

    @implementation_specific
    @non_mutating
    def describe(self) -> str:
        """Render a human-readable description of the item."""
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return self._prefix() + " " + self.number

    def __init__(self, number: str, code: str) -> None:
        self.number = number
        self.code = code


class Box(Item):
    # NOTE (mristin):
    # The two leading underscores signal a private method.
    @implementation_specific
    @non_mutating
    def __wrap(self, text: str) -> str:
        """
        Wrap :paramref:`text` in square brackets.

        It complements :meth:`_prefix`.
        """
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return "[" + text + "]"

    @implementation_specific
    @non_mutating
    def wrapped_code(self) -> str:
        """Return the code wrapped in square brackets."""
        # NOTE (mristin):
        # This implementation will not be transpiled, but is given here as reference.
        return self.__wrap(self.code)

    def __init__(self, number: str, code: str) -> None:
        Item.__init__(self, number, code)


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
