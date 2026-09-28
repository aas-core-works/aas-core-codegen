@verification
def common(text: str) -> bool:
    """Collide with the static class of the common helpers."""
    return len(text) > 0


class Common:
    """Collide with the static class of the common helpers."""

    text: str

    def __init__(self, text: str) -> None:
        self.text = text


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
