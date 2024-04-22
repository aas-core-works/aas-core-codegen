"""Generate the ProtoBuf constants corresponding to the constants of the meta-model."""

from typing import (
    Optional,
    List,
    Tuple,
)

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Error,
)
from aas_core_codegen.protobuf import (
    common as proto_common,
)

"""
TODO: proto3 does not feature constants
"""


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result: not (result[0] is not None) or result[0].endswith("\n"),
    "Trailing newline mandatory for valid end-of-files",
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable,
    namespace: proto_common.NamespaceIdentifier,
) -> Tuple[Optional[str], Optional[List[Error]]]:

    return "\n", None
