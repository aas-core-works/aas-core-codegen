"""Provide common functions shared among difference C# code generation modules."""
from typing import List, Union, Tuple, Optional

from icontract import ensure

from aas_core_csharp_codegen import intermediate, parse
from aas_core_csharp_codegen.common import Code, Error, assert_never
from aas_core_csharp_codegen.csharp import naming
from aas_core_csharp_codegen.intermediate._types import ListTypeAnnotation


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


_ATOMIC_TYPE_MAP = {
    "bool": Code("bool"),
    "int": Code("int"),
    "float": Code("float"),
    "str": Code("string")
}
assert list(_ATOMIC_TYPE_MAP.keys()) == list(parse.BUILTIN_ATOMIC_TYPES), \
    "Expected complete mapping of primitive types to implementation-specific types"


def generate_type(
        type_annotation: Union[
            intermediate.SubscriptedTypeAnnotation, intermediate.AtomicTypeAnnotation]
) -> Code:
    """
    Generate the C# type for the given type annotation.

    The type annotations are expected to be non-dangling.
    If a type does not belong to
    :attr:`aas_core_csharp_codegen.parse.BUILTIN_ATOMIC_TYPES` and
    :attr:`aas_core_csharp_codegen.parse.BUILTIN_COMPOSITE_TYPES`, it is assumed to be
    a type defined in the meta-model.
    """
    if isinstance(type_annotation, intermediate.AtomicTypeAnnotation):
        maybe_primitive_type = _ATOMIC_TYPE_MAP.get(type_annotation.identifier, None)
        if maybe_primitive_type is not None:
            return maybe_primitive_type
        # TODO: once intermediate fixed, we need to introduce naming for the symbol 🠒 dispatch here to csharp.naming
        return naming.class_name()

        return _ATOMIC_TYPE_MAP[type_annotation.identifier], None

    elif isinstance(type_annotation, intermediate.SubscriptedTypeAnnotation):
        if isinstance(type_annotation, ListTypeAnnotation):
            items, error = generate_type(type_annotation.items)
            if error is not None:
                return error

            return f"List<{}>"

            #     "List",
        #     "Sequence",
        #     "Set",
        #     "Mapping",
        #     "MutableMapping",
        #     "Optional"
        else:
            assert_never(type_annotation)

    else:
        assert_never(type_annotation)
    # TODO: impl this, then go back to _generate
    # TODO: test with general snippets, do not test in isolation
    raise NotImplementedError()
