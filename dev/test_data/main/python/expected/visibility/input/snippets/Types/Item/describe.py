def describe(self) -> str:
    """Render a human-readable description of the item."""
    return f"{self._prefix()} {self.number}"
