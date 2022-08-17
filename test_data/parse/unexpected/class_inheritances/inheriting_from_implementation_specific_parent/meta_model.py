# NOTE (mristin, 2021-07-07):
# We explicitly test that the inheritance from an implementation-specific entity
# is possible. We initially rejected the idea, and wanted to disallow such
# an inheritance chain, but changed our mind eventually due to intuition (but no
# hard reason!).


@abstract
@implementation_specific
class Parent:
    pass


@implementation_specific
class Something(Parent):
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
