"""Generate Python code for de-serialization of enumerations."""

import io
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import Error, Stripped, Identifier
from aas_core_codegen.python import common as python_common, naming as python_naming
from aas_core_codegen.python.common import INDENT as I, INDENT2 as II


def _generate_enum_from_string(
    enumeration: intermediate.Enumeration, aas_module: python_common.QualifiedModuleName
) -> Stripped:
    """Generate the functions for de-serializing enumeration from strings."""
    blocks = []  # type: List[Stripped]

    name = python_naming.enum_name(enumeration.name)

    # region From-string-map

    from_str_map_name = python_naming.constant_name(
        Identifier(f"_{enumeration.name}_from_str")
    )

    from_str_map_writer = io.StringIO()
    from_str_map_writer.write(
        f"""\
{from_str_map_name}: Mapping[str, aas_types.{name}] = {{
"""
    )

    for literal in enumeration.literals:
        literal_name = python_naming.enum_literal_name(literal.name)
        from_str_map_writer.write(
            f"{I}{python_common.string_literal(literal.value)}: "
            f"aas_types.{name}.{literal_name},\n"
        )

    from_str_map_writer.write("}")

    blocks.append(Stripped(from_str_map_writer.getvalue()))

    # endregion

    # region From-string-function

    from_str_name = python_naming.function_name(
        Identifier(f"{enumeration.name}_from_str")
    )

    from_str_writer = io.StringIO()
    from_str_writer.write(
        f"""\
def {from_str_name}(
{II}text: str
) -> Optional[aas_types.{name}]:
{I}\"\"\"
{I}Parse :paramref:`text` as string representation
{I}of :py:class:`{aas_module}.{name}`.

{I}If :paramref:`text` is not a valid string representation of a literal
{I}of :py:class:`{aas_module}.{name}`, return ``None``.

{I}:param text: to be parsed
{I}:return:
{II}the corresponding literal of :py:class:`{aas_module}.{name}`
{II}or ``None``, if :paramref:`text` invalid.
{I}\"\"\"
{I}return {from_str_map_name}.get(text, None)"""
    )

    blocks.append(Stripped(from_str_writer.getvalue()))

    # endregion

    return Stripped("\n\n\n".join(blocks))


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
    aas_module: python_common.QualifiedModuleName,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the Python code for the de-serialization of strings.

    The ``aas_module`` indicates the fully-qualified name of the base module.
    """
    blocks = [
        Stripped('"""De-serialize enumerations from string representations."""'),
        python_common.WARNING,
        Stripped(
            f"""\
from typing import (
{I}Mapping,
{I}Optional,
)

import {aas_module}.types as aas_types"""
        ),
    ]

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.Enumeration):
            continue

        blocks.append(
            _generate_enum_from_string(enumeration=our_type, aas_module=aas_module)
        )

    blocks.append(python_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue(), None
