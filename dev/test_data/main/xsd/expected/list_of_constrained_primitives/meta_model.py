from typing import List

from icontract import invariant

# NOTE (mristin):
# The XSD generator expects the constrained primitive Value data type to be defined
# since we had to hard-wire it. If we remove that hard-wiring, we can also remove
# this definition as well.

class Value_data_type(str, DBC):
    pass



@invariant(lambda self: len(self) > 0, "Non-empty")
class Name(str):
    pass


class Something:
    some_names: List[Name]

    def __init__(self, some_names: List[Name]) -> None:
        self.some_names = some_names


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
