"""Generate the Java constants corresponding to the constants of the meta-model."""
import io
import textwrap
from typing import (
    List,
    Optional,
    Tuple,
)

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Error,
    Stripped,
)
from aas_core_codegen.java import (
    common as java_common,
)
from aas_core_codegen.csharp.common import (
    INDENT as I,
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
    """
    Generate the Java code of the constants based on the symbol table.

    The ``package`` defines the AAS Java package.
    """
    constants_blocks = []  # type: List[Stripped]

    constants_writer = io.StringIO()
    constants_writer.write(
        """\
/**
 * Provide constant values of the meta-model.
 */
public class Constants {
"""
    )

    for i, constants_block in enumerate(constants_blocks):
        assert len(constants_block) > 0

        if i > 0:
            constants_writer.write("\n\n")

        constants_writer.write(textwrap.indent(constants_block, I))

    constants_writer.write("\n}")

    blocks = [
        java_common.WARNING,
        Stripped(
            f"""\
package {package}.constants;

{constants_writer.getvalue()}"""
        ),
        java_common.WARNING,
    ]  # type: List[Stripped]

    out = io.StringIO()
    for i, constants_block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        out.write(constants_block)

    out.write("\n")

    return out.getvalue(), None


# endregion
