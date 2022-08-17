@abstract
class Parent(DBC):
    pass


class Something(DBC, Parent):
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
