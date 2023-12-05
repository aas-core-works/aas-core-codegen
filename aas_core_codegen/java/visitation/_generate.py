from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen.java import (
    common as java_common,
    naming as java_naming,
)
from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Error,
    Identifier,
    Stripped,
)

# region Generate


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable, package: java_common.PackageIdentifier
) -> Tuple[Optional[List[java_common.JavaFile]], Optional[List[Error]]]:
    """
    Generate the java code of the visitors based on the intermediate representation

    The ``package`` defines the AAS Java package.
    """

    generated_classes = [
    ]  # type: List[Tuple[java_common.JavaFile, List[Error]]]

    files = [file for file, _ in generated_classes]  # type: List[java_common.JavaFile]
    errors = [
        error for _, errors in generated_classes for error in errors
    ]  # type: List[Error]

    if len(errors) > 0:
        return None, errors

    return files, None


# endregion
