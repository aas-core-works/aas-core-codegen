from icontract import DBC, invariant


@verification
def matches_something(text: str) -> bool:
    """Check that :paramref:`text` is something."""
    pattern = "^something$"
    return match(pattern, text) is not None


@verification
def _matches_something_re(text: str) -> bool:
    """Collide with the regular expression of :func:`matches_something` in Go."""
    return len(text) > 0


@verification
def _verify_json_value(text: str) -> bool:
    """Collide with the helper to verify JSON-able values in Go."""
    return len(text) > 1


@invariant(lambda self: matches_something(self.text), "Text must be something")
@invariant(lambda self: _matches_something_re(self.text), "Text must not be empty")
@invariant(lambda self: _verify_json_value(self.text), "Text must be long")
class Something(DBC):
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
