"""Provide common functions shared among difference C# code generation modules."""
from typing import List, Union

from icontract import ensure

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Code


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


def generate_type(
        type_annotation: Union[
            intermediate.SubscriptedTypeAnnotation, intermediate.AtomicTypeAnnotation]
) -> Code:
    """
    Generate the C# type for the given type annotation.

    This function is oblivious whether the type is valid.
    """
    # TODO: impl this, then go back to _generate
    # TODO: test with general snippets, do not test in isolation
    raise NotImplementedError()
