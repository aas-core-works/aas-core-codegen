class Some_enum(Enum, SomeUnexpectedClass):
    some_literal = "SomeLiteral"


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
