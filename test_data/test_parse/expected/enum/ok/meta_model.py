class Some_enum(Enum):
    """
    Represent something.

        Indented.
    """

    LITERAL = "Literal"
    """This is a literal."""

    LITERAL_WITHOUT_DOC = "LiteralWithoutDoc"


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
