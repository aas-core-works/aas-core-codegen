"""
Understand the verification functions.

The classes
:py:class:`aas_core_codegen.intermediate._types.ImplementationSpecificVerification`
and :py:class:`aas_core_codegen.intermediate._types.PatternVerification` had to be
defined in :py:mod:`aas_core_codegen.intermediate._types` to avoid circular imports.
"""
import ast
from typing import Optional

from icontract import require

from aas_core_codegen.intermediate._types import PatternVerification
from aas_core_codegen import parse
from aas_core_codegen.parse import (
    tree as parse_tree
)


# fmt: off
@require(
    lambda parsed:
    not parsed.is_implementation_specific,
    "Don't try to understand an implementation-specific verification function"
)
@require(
    lambda parsed:
    parsed.verification,
    "Understand only verification functions"
)
@require(
    lambda parsed:
    len(parsed.arguments) == 1
    and isinstance(parsed.arguments[0].type_annotation, parse.AtomicTypeAnnotation)
    and parsed.arguments[0].type_annotation.identifier == 'str',
    "Understand only "
)
# fmt: on
def try_to_understand_pattern_verification(
        parsed: parse.Method
) -> Optional[PatternVerification]:
    """
    Try to understand the given verification function as a pattern matching function.

    :param parsed: Verification function as parsed in the parsing phase
    :return: pattern verification, if understood
    """
    # Understand only functions that take a single string argument
    if not (
            len(parsed.arguments) == 1
            and isinstance(
                parsed.arguments[0].type_annotation,
                parse.AtomicTypeAnnotation)
            and parsed.arguments[0].type_annotation.identifier == 'str'
    ):
        return None

    # We need to return something,
    if not (
            parsed.returns is not None
            and isinstance(parsed.returns, parse.AtomicTypeAnnotation)
            and parsed.returns.identifier == 'bool'
    ):
        return None

    # TODO: implement this till the end once we understand the pattern matching statements in _rules
