"""Provide data structures for implementations used for all implementation languages."""
import re
from typing import cast, Mapping

from icontract import require

from aas_core_csharp_codegen.common import Stripped

IMPLEMENTATION_KEY_RE = re.compile('[a-zA-Z_][a-zA-Z_0-9]*(/[a-zA-Z_][a-zA-Z_0-9]*)*')


class ImplementationKey(str):
    """
    Represent a key in the map of specific implementations.

    A key follows the schema:

    * ``{symbol name}`` for the symbols with specific implementation,
    * ``{symbol name}/{method name}`` for the methods with the specific implementation,
    * ``{general snippet identifier}`` for snippets which are not tied to a symbol
    """

    @require(lambda key: IMPLEMENTATION_KEY_RE.fullmatch(key))
    def __new__(cls, key: str) -> 'ImplementationKey':
        return cast(ImplementationKey, key)


SpecificImplementations = Mapping[ImplementationKey, Stripped]
