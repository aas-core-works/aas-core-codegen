from typing import List

from aas_core_meta.marker import JSONObject


class Something(DBC):
    values: List[JSONObject[int]]

    def __init__(self, values: List[JSONObject[int]]) -> None:
        self.values = values


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
