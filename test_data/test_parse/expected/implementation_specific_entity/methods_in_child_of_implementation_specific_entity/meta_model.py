# NOTE (mristin, 2021-06-30):
# This snippet is OK as the generated code will be correct even though we do not
# know what a constructor of ``Abstract`` class looks like.
#
# We have to see in the future how this construct plays out in practice.

@abstract
@implementation_specific
class Abstract:
    pass


class Something(Abstract):
    def do_something(self) -> None:
        pass
