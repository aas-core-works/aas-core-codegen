# NOTE (mristin, 2022-06-19):
# We originally wrote this test to check that the concrete class with descendants
# also implements the interface.


class Parent:
    pass


class Child(Parent):
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
