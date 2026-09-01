from typing import Annotated, Optional

from icontract import DBC

from aas_core_meta.marker import json_name, xml_name


class Query_condition(DBC):
    """Represent a single condition of a query expression."""

    eq: Annotated[Optional[str], json_name("$eq")]
    """Operand to be checked for equality."""

    not_eq: Annotated[Optional[str], json_name("$ne"), xml_name("not-eq")]
    """Operand to be checked for inequality."""

    def __init__(
        self,
        eq: Optional[str] = None,
        not_eq: Optional[str] = None,
    ) -> None:
        self.eq = eq
        self.not_eq = not_eq


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
