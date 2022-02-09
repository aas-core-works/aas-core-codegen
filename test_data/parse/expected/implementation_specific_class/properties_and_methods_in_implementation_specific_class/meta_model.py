# The parser accepts properties and methods in implementation-specific entities
# although the code generator will disregard them.
#
# This is useful, for example, for linting or for visualizing the meta-model
# even though no code is generated based on these properties and methods.


@implementation_specific
class Something:
    x: int

    def do_something(self) -> None:
        pass


__book_url__ = "dummy"
__book_version__ = "dummy"
