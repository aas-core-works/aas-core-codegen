"""Provide common functions shared among difference C# code generation modules."""
import re
import textwrap
from typing import List, Union, cast, Iterator

from icontract import ensure, require

from aas_core_codegen import intermediate
from aas_core_codegen.common import Stripped, assert_never
from aas_core_codegen.csharp import naming as csharp_naming


@ensure(lambda result: result.startswith('"'))
@ensure(lambda result: result.endswith('"'))
def string_literal(text: str) -> str:
    """Generate a C# string literal from the ``text``."""
    escaped = []  # type: List[str]

    for character in text:
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
        else:
            escaped.append(character)

    return '"{}"'.format("".join(escaped))


PRIMITIVE_TYPE_MAP = {
    intermediate.PrimitiveType.BOOL: Stripped("bool"),
    intermediate.PrimitiveType.INT: Stripped("int"),
    intermediate.PrimitiveType.FLOAT: Stripped("float"),
    intermediate.PrimitiveType.STR: Stripped("string"),
    intermediate.PrimitiveType.BYTEARRAY: Stripped("byte[]"),
}

# noinspection PyTypeChecker
assert sorted(literal.value for literal in PRIMITIVE_TYPE_MAP.keys()) == sorted(
    literal.value for literal in intermediate.PrimitiveType
), (
    "Expected complete mapping of primitive to implementation-specific types"
)  # type: ignore


def generate_type(
    type_annotation: Union[
        intermediate.SubscriptedTypeAnnotation, intermediate.AtomicTypeAnnotation
    ],
    ref_association: intermediate.Class,
) -> Stripped:
    """
    Generate the C# type for the given type annotation.

    The ``ref_association`` describes how the references should be represented.
    """
    # TODO-BEFORE-RELEASE (mristin, 2021-12-13): test in isolation
    if isinstance(type_annotation, intermediate.AtomicTypeAnnotation):
        if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
            return PRIMITIVE_TYPE_MAP[type_annotation.a_type]

        elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
            symbol = type_annotation.symbol

            if isinstance(symbol, intermediate.Enumeration):
                return Stripped(csharp_naming.enum_name(type_annotation.symbol.name))

            elif isinstance(symbol, intermediate.ConstrainedPrimitive):
                return PRIMITIVE_TYPE_MAP.get(symbol.constrainee)

            elif isinstance(symbol, intermediate.Class):
                # NOTE (mristin, 2021-12-26):
                # Always prefer an interface to allow for discrimination. If there is
                # an interface based on the class, it means that there are one or more
                # descendants.

                if symbol.interface:
                    return Stripped(csharp_naming.interface_name(symbol.name))
                else:
                    return Stripped(csharp_naming.class_name(symbol.name))

            else:
                assert_never(symbol)

        else:
            assert_never(type_annotation)

    elif isinstance(type_annotation, intermediate.SubscriptedTypeAnnotation):
        if isinstance(type_annotation, intermediate.ListTypeAnnotation):
            item_type = generate_type(
                type_annotation=type_annotation.items, ref_association=ref_association
            )

            return Stripped(f"List<{item_type}>")

        elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
            value = generate_type(
                type_annotation=type_annotation.value, ref_association=ref_association
            )
            return Stripped(f"{value}?")

        elif isinstance(type_annotation, intermediate.RefTypeAnnotation):
            if ref_association.interface is not None:
                return Stripped(csharp_naming.interface_name(ref_association.name))
            else:
                return Stripped(csharp_naming.class_name(ref_association.name))

        else:
            assert_never(type_annotation)
    else:
        assert_never(type_annotation)


INDENT = "    "
INDENT2 = INDENT * 2
INDENT3 = INDENT * 3
INDENT4 = INDENT * 4

NAMESPACE_IDENTIFIER_RE = re.compile(
    r"[a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)"
)


class NamespaceIdentifier:
    """Capture a namespace identifier."""

    @require(lambda identifier: NAMESPACE_IDENTIFIER_RE.fullmatch(identifier))
    def __new__(cls, identifier: str) -> "NamespaceIdentifier":
        return cast(NamespaceIdentifier, identifier)


WARNING = Stripped(
    textwrap.dedent(
        """\
    /*
     * This code has been automatically generated by aas-core-codegen.
     * Do NOT edit or append.
     */"""
    )
)


def over_enumerations_classes_and_interfaces(
    symbol_table: intermediate.SymbolTable,
) -> Iterator[
    Union[intermediate.Enumeration, intermediate.ConcreteClass, intermediate.Interface]
]:
    """
    Iterate over all enumerations, concrete classes and interfaces.

    These intermediate structures form the base of the C# code.
    """
    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            yield symbol
        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            pass
        elif isinstance(symbol, intermediate.AbstractClass):
            yield symbol.interface
        elif isinstance(symbol, intermediate.ConcreteClass):
            if symbol.interface:
                yield symbol.interface

            yield symbol
        else:
            assert_never(symbol)
