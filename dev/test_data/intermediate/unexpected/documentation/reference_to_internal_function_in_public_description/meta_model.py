@verification
def _is_something(text: str) -> bool:
    return len(text) > 0


class Something:
    """Represent something checked with :func:`_is_something`."""

    text: str

    def __init__(self, text: str) -> None:
        self.text = text


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
