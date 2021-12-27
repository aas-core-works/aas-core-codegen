@abstract
class Parent(DBC):
    pass


class Something(DBC, Parent):
    pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
