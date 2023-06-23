"""Generate Python code of common functions by including the code directly."""

import io

from icontract import ensure

from aas_core_codegen.common import (
    Stripped,
)
from aas_core_codegen.python import (
    common as python_common,
)
from aas_core_codegen.python.common import (
    INDENT as I,
)


# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(aas_module: python_common.QualifiedModuleName) -> str:
    """
    Generate the Python code for common functions.

    The ``aas_module`` indicates the fully-qualified name of the base module.
    """
    blocks = [
        Stripped('"""Provide common functions shared among the modules."""'),
        python_common.WARNING,
        Stripped(
            f"""\
from typing import (
{I}NoReturn
)"""
        ),
        Stripped(
            f"""\
def assert_never(value: NoReturn) -> NoReturn:
{I}\"\"\"
{I}Signal to mypy to perform an exhaustive matching.

{I}Please see the following page for more details:
{I}https://hakibenita.com/python-mypy-exhaustive-checking
{I}\"\"\"
{I}assert False, f"Unhandled value: {{value}} ({{type(value).__name__}})\""""
        ),
        Stripped(
            f"""\
// Concatenate the strings together as a faster version of [fmt.Sprint].
func Concat(strs ...string) string {{
{I}return strings.Join(strs, "")
}}"""
        ),
        python_common.WARNING,
    ]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()
