"""Generate the Java constants corresponding to the constants of the meta-model."""
from typing import (
    List,
    Optional,
    Tuple,
)

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Error,
)
from aas_core_codegen.java import (
    common as java_common,
)

# region Generation


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable,
    package: java_common.PackageIdentifier,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    raise NotImplementedError


# endregion
