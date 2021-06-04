# The parser accepts properties and methods in implementation-specific entities
# although the code generator will disregard them.
#
# This is useful, for example, for linting or for visualizing the meta-model
# even though no code is generated based on these properties and methods.

@abstract
@implementation_specific
class Abstract:
    x: int

    def do_something(self) -> None:
        pass
