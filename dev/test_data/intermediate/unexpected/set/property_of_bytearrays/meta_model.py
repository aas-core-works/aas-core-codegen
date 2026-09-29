from typing import Optional, Set


class Something(DBC):
    blobs: Optional[Set[bytearray]]

    def __init__(self, blobs: Optional[Set[bytearray]] = None) -> None:
        self.blobs = blobs


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
