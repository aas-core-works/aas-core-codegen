from icontract import DBC

from aas_core_meta.marker import verification


class Something(DBC):
    interface: str
    type: str
    range: str
    void: str

    def __init__(self, interface: str, type: str, range: str, void: str) -> None:
        self.interface = interface
        self.type = type
        self.range = range
        self.void = void


@verification
def interface(something: str) -> bool:
    return True


@verification
def void(something: str) -> bool:
    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
