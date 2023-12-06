"""Generate Java code for de/serialization based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Error,
    Stripped,
    Identifier,
)
from aas_core_codegen.java import (
    common as java_common,
    naming as java_naming,
)
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
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
    symbol_table: intermediate.SymbolTable, package: java_common.PackageIdentifier
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the Java code for the general serialization.

    The ``package`` defines the AAS Java package.
    """
    imports = [
        Stripped("import java.util.Collections;"),
        Stripped("import java.util.HashMap;"),
        Stripped("import java.util.Map;"),
        Stripped("import java.util.Optional;"),
        Stripped(f"import {package}.types.enums.*;"),
    ]  # type: List[Stripped]

    blocks = [
        java_common.WARNING,
        Stripped(f"package {package}.stringification;"),
        Stripped("\n".join(imports)),
    ]


    writer = io.StringIO()
    writer.write(
        """\
public class Stringification {
"""
    )


    writer.write(f"\n}}")

    blocks.append(Stripped(writer.getvalue()))

    blocks.append(java_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        assert not block.startswith("\n")
        assert not block.endswith("\n")
        out.write(block)

    out.write("\n")

    return out.getvalue(), None
