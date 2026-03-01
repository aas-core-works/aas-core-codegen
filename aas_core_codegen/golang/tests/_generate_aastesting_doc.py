"""Generate the documentation for aastesting package."""

import io
from typing import List

from icontract import ensure

from aas_core_codegen.common import (
    Stripped,
)
from aas_core_codegen.golang import common as golang_common


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate() -> str:
    """Generate the documentation for aastesting package."""
    blocks = [
        Stripped(
            """\
// Package aastesting provides the functions and data structures shared across
// different tests.
package aastesting"""
        ),
        golang_common.WARNING,
    ]  # type: List[Stripped]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
