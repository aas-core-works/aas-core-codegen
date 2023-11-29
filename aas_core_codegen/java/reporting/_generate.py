"""Generate Java code for reporting errors by including the code directly."""

import io
from typing import List

from icontract import ensure

from aas_core_codegen.common import (
    Stripped,
)
from aas_core_codegen.java import (
    common as java_common,
)

# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(package: java_common.PackageIdentifier) -> str:
    """
    Generate the Java code for reporting errors.

    The ``package`` defines the AAS Java package.
    """

    blocks = []  # type: List[Stripped]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        assert not block.startswith("\n")
        assert not block.endswith("\n")
        writer.write(block)

    writer.write("\n")

    return writer.getvalue()
