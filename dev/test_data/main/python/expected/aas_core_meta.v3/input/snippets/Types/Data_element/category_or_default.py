def category_or_default(self) -> str:
    """Return the :py:attr:`category` if set or the default value otherwise."""
    return self.category if self.category else "VARIABLE"
