"""Generate Java code for enhancing model classes."""

import io
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate, specific_implementations
from aas_core_codegen.common import (
    Error,
)
from aas_core_codegen.java import (
    common as java_common,
)

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
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[List[java_common.JavaFile]], Optional[List[Error]]]:
    """
    Generate the Java code for enhancing model classes with custom wraps.

    The ``package`` defines the AAS Java package.
    """

    errors = []  # type: List[Error]

    return [], None
