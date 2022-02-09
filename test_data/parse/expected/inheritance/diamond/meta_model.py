@abstract
class Another_grand_parent(DBC):
    pass


@abstract
class Grand_parent(DBC):
    pass


@abstract
class Parent(DBC, Grand_parent, Another_grand_parent):
    pass


@abstract
class Another_parent(DBC, Grand_parent, Another_grand_parent):
    pass


class Something(DBC, Parent, Another_parent):
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
