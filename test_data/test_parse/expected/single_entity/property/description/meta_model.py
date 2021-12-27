class Something:
    """Represent something."""

    some_property: int
    """some property"""

    another_property: str

    yet_another_property: str
    """yet another property"""


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
