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


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
