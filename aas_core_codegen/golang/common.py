"""Provide common functions shared among different Go code generation modules."""
import io
import math
from typing import List, Tuple, Optional

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import Stripped, assert_never, Identifier
from aas_core_codegen.golang import (
    naming as golang_naming,
    pointering as golang_pointering,
)


@ensure(lambda result: result.startswith('"'))
@ensure(lambda result: result.endswith('"'))
def string_literal(text: str) -> Stripped:
    """Generate a Go string literal from the ``text``."""
    escaped = []  # type: List[str]

    for character in text:
        code_point = ord(character)

        if character == "\a":
            escaped.append("\\a")
        elif character == "\b":
            escaped.append("\\b")
        elif character == "\f":
            escaped.append("\\f")
        elif character == "\n":
            escaped.append("\\n")
        elif character == "\r":
            escaped.append("\\r")
        elif character == "\t":
            escaped.append("\\t")
        elif character == "\v":
            escaped.append("\\v")
        elif character == '"':
            escaped.append('\\"')
        elif character == "\\":
            escaped.append("\\\\")
        elif code_point < 32:
            # Non-printable ASCII characters
            escaped.append(f"\\x{ord(character):x}")
        elif 255 < code_point < 65536:
            # Above ASCII
            escaped.append(f"\\u{ord(character):04x}")
        elif code_point >= 65536:
            # Above Unicode Binary Multilingual Pane
            escaped.append(f"\\U{ord(character):08x}")
        else:
            escaped.append(character)

    return Stripped('"{}"'.format("".join(escaped)))


def needs_escaping(text: str) -> bool:
    """Check whether the ``text`` contains a character that needs escaping."""
    for character in text:
        if character == "\a":
            return True
        elif character == "\b":
            return True
        elif character == "\f":
            return True
        elif character == "\n":
            return True
        elif character == "\r":
            return True
        elif character == "\t":
            return True
        elif character == "\v":
            return True
        elif character == '"':
            return True
        elif character == "\\":
            return True
        else:
            pass

    return False


def boolean_literal(value: bool) -> Stripped:
    """Generate the boolean literal corresponding to the ``value``."""
    return Stripped("true") if value else Stripped("false")


def float_literal(value: float) -> Stripped:
    """Generate the float literal.

    We assume that the precision of the literal is not critical and rely on
    Python's ``str(.)`` function. However, if you want to specify the exact
    number, you have to format the number yourself, probably using G17 representation.
    """
    if math.isnan(value):
        return Stripped("math.NaN")
    if value == math.inf:
        return Stripped("math.Inf(1)")
    elif value == -math.inf:
        return Stripped("math.Inf(-1)")
    else:
        return Stripped(str(value))


# NOTE (mristin, 2023-01-13):
# See: https://stackoverflow.com/questions/19094704/indentation-in-go-tabs-or-spaces
INDENT = "\t"


def bytes_literal(value: bytes) -> Tuple[Stripped, bool]:
    """
    Generate an expression representing the ``value``.

    If there are more than 8 bytes, a multi-line expression is returned.

    :param value: to be represented
    :return: (Golang expression, is multi-line)
    """
    if len(value) == 0:
        return Stripped("[...]byte{}"), False

    writer = io.StringIO()

    if len(value) <= 8:
        items_joined = ", ".join(f"0x{byte:02x}" for byte in value)
        return Stripped(f"[...]byte{{{items_joined}}}"), False
    else:
        writer.write(
            """\
[...]byte {"""
        )

        for start in range(0, len(value), 8):
            if start == 0:
                writer.write(f"\n{INDENT}")
            else:
                writer.write(f",\n{INDENT}")

            end = min(start + 8, len(value))

            assert start < end

            for i, byte in enumerate(value[start:end]):
                if i > 0:
                    writer.write(", ")

                writer.write(f"0x{byte:02x}")

        writer.write("\n}")

        return Stripped(writer.getvalue()), True


PRIMITIVE_TYPE_MAP = {
    intermediate.PrimitiveType.BOOL: Stripped("bool"),
    intermediate.PrimitiveType.INT: Stripped("int64"),
    intermediate.PrimitiveType.FLOAT: Stripped("float64"),
    intermediate.PrimitiveType.STR: Stripped("string"),
    intermediate.PrimitiveType.BYTEARRAY: Stripped("[]byte"),
}


def _assert_all_primitive_types_are_mapped() -> None:
    """Assert that we have explicitly mapped all the primitive types to Go."""
    all_primitive_literals = set(literal.value for literal in PRIMITIVE_TYPE_MAP)

    mapped_primitive_literals = set(
        literal.value for literal in intermediate.PrimitiveType
    )

    all_diff = all_primitive_literals.difference(mapped_primitive_literals)
    mapped_diff = mapped_primitive_literals.difference(all_primitive_literals)

    messages = []  # type: List[str]
    if len(mapped_diff) > 0:
        messages.append(
            f"More primitive maps are mapped than there were defined "
            f"in the ``intermediate._types``: {sorted(mapped_diff)}"
        )

    if len(all_diff) > 0:
        messages.append(
            f"One or more primitive types in the ``intermediate._types`` were not "
            f"mapped in PRIMITIVE_TYPE_MAP: {sorted(all_diff)}"
        )

    if len(messages) > 0:
        raise AssertionError("\n\n".join(messages))


_assert_all_primitive_types_are_mapped()

TYPES_PACKAGE = Identifier("aastypes")
CONSTANTS_PACKAGE = Identifier("aasconstants")
VERIFICATION_PACKAGE = Identifier("aasverification")


def generate_type(
    type_annotation: intermediate.TypeAnnotationUnion,
    types_package: Optional[Identifier] = None,
) -> Stripped:
    """
    Generate the Go type for the given type annotation.

    If ``types_package`` is specified, it is prepended to all our types.
    """
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return PRIMITIVE_TYPE_MAP[type_annotation.a_type]

    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        our_type = type_annotation.our_type

        if isinstance(our_type, intermediate.Enumeration):
            enum_name = golang_naming.enum_name(type_annotation.our_type.name)
            if types_package is None:
                return enum_name

            return Stripped(f"{types_package}.{enum_name}")

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            return PRIMITIVE_TYPE_MAP[our_type.constrainee]

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            # NOTE (mristin, 2023-03-28):
            # We always refer to interfaces even in cases of concrete classes without
            # concrete descendants since we want to allow enhancing.
            interface_name = golang_naming.interface_name(our_type.name)

            if types_package is None:
                return interface_name

            return Stripped(f"{types_package}.{interface_name}")

    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        item_type = generate_type(
            type_annotation=type_annotation.items, types_package=types_package
        )

        return Stripped(f"[]{item_type}")

    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        value_type = generate_type(
            type_annotation=type_annotation.value, types_package=types_package
        )

        if golang_pointering.is_pointer_type(type_annotation):
            return Stripped(f"*{value_type}")

        return value_type

    else:
        assert_never(type_annotation)

    raise AssertionError("Should not have gotten here")


INDENT2 = INDENT * 2
INDENT3 = INDENT * 3
INDENT4 = INDENT * 4
INDENT5 = INDENT * 5
INDENT6 = INDENT * 6

WARNING = Stripped(
    """\
// This code has been automatically generated by aas-core-codegen.
// Do NOT edit or append."""
)


class GeneratorForLoopVariables:
    """
    Generate a unique variable name based on ``item`` stem.

    >>> generator = GeneratorForLoopVariables()

    >>> next(generator)
    'v'

    >>> next(generator)
    'v1'

    >>> next(generator)
    'v2'
    """

    def __init__(self) -> None:
        """Initialize with the zero counter."""
        self.counter = 0

    def __next__(self) -> Identifier:
        """Generate the next variable name."""
        if self.counter == 0:
            result = Identifier("v")
        else:
            result = Identifier(f"v{self.counter}")

        self.counter += 1

        return result
