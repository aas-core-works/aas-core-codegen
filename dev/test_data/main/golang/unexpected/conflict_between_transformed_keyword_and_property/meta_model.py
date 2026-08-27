"""
We transform the Go keywords in the resulting code so that they do not conflict. However,
this can also conflict with properties where the transformation coincides with the
camel-casing.

In this test, we explicitly test for such conflicts.
"""

class Something:
    interface: str
    interfac_e: str

    def __init__(self, interface: str, interfac_e: str) -> None:
        self.interface = interface
        self.interfac_e = interfac_e

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
