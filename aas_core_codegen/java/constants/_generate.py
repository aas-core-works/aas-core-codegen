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
    assert_never,
    Error,
    Stripped,
)
from aas_core_codegen.java import (
    common as java_common,
    naming as java_naming,
)
from aas_core_codegen.csharp.common import (
    INDENT as I,
)

# region Generation


def _byte_array_as_expr(value: bytearray) -> Stripped:
    """Return a multi-line java code representing the ``value''."""
    writer = io.StringIO()

    writer.write("new byte[] {")

    for i, byte in enumerate(value):
        if i > 0:
            if i % 8 == 0:
                writer.write(",\n")
            else:
                writer.write(", ")

        writer.write(f"(byte) 0x{byte:02x}")

    writer.write("\n}")

    return Stripped(writer.getvalue())


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_constant_primitive(
        constant: intermediate.ConstantPrimitive,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition of a constant primitive."""
    constant_name = java_naming.property_name(constant.name)

    assert constant.a_type in java_common.PRIMITIVE_TYPE_MAP

    java_type = java_common.PRIMITIVE_TYPE_MAP[constant.a_type]

    literal = None  # type: Optional[Stripped]

    if constant.a_type is intermediate.PrimitiveType.BOOL:
        literal = Stripped("true") if constant.value else Stripped("false")

    elif constant.a_type is intermediate.PrimitiveType.INT:
        literal = Stripped(str(constant.value))

    elif constant.a_type is intermediate.PrimitiveType.FLOAT:
        literal = Stripped(str(constant.value))

    elif constant.a_type is intermediate.PrimitiveType.STR:
        assert isinstance(constant.value, str)
        literal = java_common.string_literal(constant.value)

    elif constant.a_type is intermediate.PrimitiveType.BYTEARRAY:
        assert isinstance(constant.value, bytearray)
        literal = _byte_array_as_expr(value=constant.value)

    else:
        assert_never(constant.a_type)

    assert literal is not None

    return Stripped(f"public static const {java_type} {constant_name} = {literal};"), None


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

    errors = []  # type: List[Error]

    for constant in symbol_table.constants:
        constants_block = None  # type: Optional[Stripped]
        error = None  # type: Optional[Error]

        if isinstance(constant, intermediate.ConstantPrimitive):
            constants_block, error = _generate_constant_primitive(constant)
        elif isinstance(constant, intermediate.ConstantSetOfPrimitives):
            print("TODO: Constant generation for ConstantSetOfPrimitives types not implemented yet.")
            continue
        elif isinstance(constant, intermediate.ConstantSetOfEnumerationLiterals):
            print("TODO: Constant generation for ConstantSetOfEnumerationLiterals types not implemented yet.")
            continue
        else:
            assert_never(constant)

        if error is not None:
            errors.append(error)
            continue

        assert constants_block is not None
        constants_blocks.append(constants_block)

    if len(errors) > 0:
        return None, errors

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
