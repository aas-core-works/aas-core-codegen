class Some_enum(Enum):
    some_literal = "some_literal"


class Something(Some_enum):
    pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
