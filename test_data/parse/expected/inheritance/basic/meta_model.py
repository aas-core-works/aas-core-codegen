@abstract
class Parent(DBC):
    pass


class Something(DBC, Parent):
    pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
