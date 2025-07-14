from typing import List
from icontract import DBC


class Value_data_type(str, DBC):
    """
    any XSD simple type as specified via :class:`Data_type_def_XSD`
    """


class Data_type_def_XSD(Enum):
    """
    Enumeration listing all XSD anySimpleTypes
    """

    Boolean = "xs:boolean"
    Date = "xs:date"
    Integer = "xs:integer"
    String = "xs:string"


class My_class:
    pass


class List_of_primitives:
    foo: str
    strings: List[str]
    integers: List[int]
    booleans: List[bool]
    classes: List[My_class]

    def __init__(
        self,
        foo: str,
        strings: List[str],
        integers: List[int],
        booleans: List[bool],
        classes: List[My_class],
    ) -> None:
        self.foo = foo
        self.strings = strings
        self.integers = integers
        self.booleans = booleans
        self.classes = classes


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
