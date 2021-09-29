"""Provide common functions shared among difference C# code generation modules."""
import re
from typing import List, Union, cast

from icontract import ensure, require

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Stripped, assert_never
from aas_core_csharp_codegen.csharp import naming


@ensure(lambda result: result.startswith('"'))
@ensure(lambda result: result.endswith('"'))
def string_literal(text: str) -> str:
    """Generate a C# string literal from the ``text``."""
    escaped = []  # type: List[str]

    for character in text:
        if character == '\a':
            escaped.append('\\a')
        elif character == '\b':
            escaped.append('\\b')
        elif character == '\f':
            escaped.append('\\f')
        elif character == '\n':
            escaped.append('\\n')
        elif character == '\r':
            escaped.append('\\r')
        elif character == '\t':
            escaped.append('\\t')
        elif character == '\v':
            escaped.append('\\v')
        elif character == '"':
            escaped.append('\\"')
        elif character == "\\":
            escaped.append('\\\\')
        else:
            escaped.append(character)

    return '"{}"'.format("".join(escaped))


_BUILTING_ATOMIC_TYPE_MAP = {
    intermediate.BuiltinAtomicType.BOOL: Stripped("bool"),
    intermediate.BuiltinAtomicType.INT: Stripped("int"),
    intermediate.BuiltinAtomicType.FLOAT: Stripped("float"),
    intermediate.BuiltinAtomicType.STR: Stripped("string")
}

# noinspection PyTypeChecker
assert (
        sorted(literal.value for literal in _BUILTING_ATOMIC_TYPE_MAP.keys())
        == sorted(literal.value for literal in intermediate.BuiltinAtomicType)
), (
    "Expected complete mapping of built-in types to implementation-specific types"
)  # type: ignore


def generate_type(
        type_annotation: Union[
            intermediate.SubscriptedTypeAnnotation, intermediate.AtomicTypeAnnotation]
) -> Stripped:
    """Generate the C# type for the given type annotation."""
    # TODO: test with general snippets, do not test in isolation
    if isinstance(type_annotation, intermediate.AtomicTypeAnnotation):
        if isinstance(type_annotation, intermediate.BuiltinAtomicTypeAnnotation):
            return _BUILTING_ATOMIC_TYPE_MAP[type_annotation.a_type]

        elif isinstance(type_annotation, intermediate.OurAtomicTypeAnnotation):
            if isinstance(type_annotation.symbol, intermediate.Enumeration):
                return Stripped(naming.enum_name(type_annotation.symbol.name))

            elif isinstance(type_annotation.symbol, intermediate.Interface):
                return Stripped(naming.interface_name(type_annotation.symbol.name))

            elif isinstance(type_annotation.symbol, intermediate.Class):
                return Stripped(naming.class_name(type_annotation.symbol.name))

            else:
                assert_never(type_annotation.symbol)

        else:
            assert_never(type_annotation)

    elif isinstance(type_annotation, intermediate.SubscriptedTypeAnnotation):
        if isinstance(type_annotation, intermediate.ListTypeAnnotation):
            return Stripped(f"List<{generate_type(type_annotation.items)}>")

        elif isinstance(type_annotation, intermediate.SequenceTypeAnnotation):
            return Stripped(
                f"ReadOnlyCollection<{generate_type(type_annotation.items)}>")

        elif isinstance(type_annotation, intermediate.MappingTypeAnnotation):
            keys = generate_type(type_annotation.keys)
            values = generate_type(type_annotation.values)
            return Stripped(f"ReadOnlyDictionary<{keys}, {values}>")

        elif isinstance(type_annotation, intermediate.MutableMappingTypeAnnotation):
            keys = generate_type(type_annotation.keys)
            values = generate_type(type_annotation.values)
            return Stripped(f"Dictionary<{keys}, {values}>")

        elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
            value = generate_type(type_annotation.value)
            return Stripped(f"{value}?")

        else:
            assert_never(type_annotation)
    else:
        assert_never(type_annotation)


INDENT = "    "

NAMESPACE_IDENTIFIER_RE = re.compile(
    r'[a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)')


class NamespaceIdentifier:
    """Capture a namespace identifier."""

    @require(lambda identifier: NAMESPACE_IDENTIFIER_RE.fullmatch(identifier))
    def __new__(cls, identifier: str) -> 'NamespaceIdentifier':
        return cast(NamespaceIdentifier, identifier)
