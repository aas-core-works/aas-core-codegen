"""
Understand the verification functions.

The classes
:py:class:`aas_core_codegen.intermediate._types.ImplementationSpecificVerification`
and :py:class:`aas_core_codegen.intermediate._types.PatternVerification` had to be
defined in :py:mod:`aas_core_codegen.intermediate._types` to avoid circular imports.
"""
import ast
from typing import Optional, Tuple

from icontract import require, ensure

from aas_core_codegen.intermediate._types import PatternVerification
from aas_core_codegen import parse
from aas_core_codegen.common import Error
from aas_core_codegen.parse import (
    tree as parse_tree
)


# fmt: off
@require(
    lambda parsed:
    parsed.verification,
    "Understand only verification functions"
)
@ensure(
    lambda result:
    not (result[2] is None)
    or (
            (result[1] is not None)
            and ((result[0] is not None) ^ result[1])
    ),
    "Valid match and found if no error"
)
@ensure(
    lambda result:
    not (result[2] is not None)
    or (result[0] is None and result[1] is None),
    "No match and found if error"
)
# fmt: on
def try_to_understand(
        parsed: parse.UnderstoodMethod
) -> Tuple[Optional[PatternVerification], Optional[bool], Optional[Error]]:
    """
    Try to understand the given verification function as a pattern matching function.

    :param parsed: Verification function as parsed in the parsing phase
    :return: pattern verification, if understood

    We return an error if the method looks like a pattern matching, but has a slightly
    unexpected form (*e.g.*, flags in the call to ``match(...)``).
    """
    # Understand only functions that take a single string argument
    if not (
            len(parsed.arguments) == 1
            and isinstance(
        parsed.arguments[0].type_annotation,
        parse.AtomicTypeAnnotation)
            and parsed.arguments[0].type_annotation.identifier == 'str'
    ):
        return None, False, None

    # We need to return something,
    if not (
            parsed.returns is not None
            and isinstance(parsed.returns, parse.AtomicTypeAnnotation)
            and parsed.returns.identifier == 'bool'
    ):
        return None, False, None

    print(f"parsed.body is {parsed.body!r}")  # TODO: debug

    if len(parsed.body) == 0:
        return None, False, None

    if not isinstance(parsed.body[-1], parse_tree.Return):
        return None, False, None

    return_node = parsed.body[-1]
    assert isinstance(return_node, parse_tree.Return)

    # TODO-BEFORE-RELEASE (mristin, 2021-12-19): test this
    if (
            isinstance(return_node.value, parse_tree.FunctionCall)
            and return_node.value.name == 'match'
    ):
        return (
            None,
            None,
            Error(
                return_node.original_node,
                "The ``match`` function returns a re.Match object, "
                "but this function expected the return value to be a boolean. "
                "Did you maybe want to write ``return match(...) is not None``?"
            )
        )

    if not (
            isinstance(return_node.value, parse_tree.IsNotNone)
            and isinstance(return_node.value.value, parse_tree.FunctionCall)
            and return_node.value.value.name == 'match'
    ):
        return None, False, None

    # NOTE (mristin, 2021-12-19):
    # From here on we return errors. The verification function looks like a pattern
    # matching so if we can not match (no pun intended), we should signal the user that
    # something was unexpected.

    match_call = return_node.value.value
    assert isinstance(match_call, parse_tree.FunctionCall)
    assert match_call.name == 'match'

    # TODO-BEFORE-RELEASE (mristin, 2021-12-19): test this
    if len(match_call.args) < 2:
        return (
            None,
            None,
            Error(
                match_call.original_node,
                f"The ``match`` function expects two arguments "
                f"(pattern and the text to be matched), "
                f"but you provided {len(match_call.args)} argument(s)"
            )
        )

    # TODO-BEFORE-RELEASE (mristin, 2021-12-19): test this
    if len(match_call.args) > 2:
        return (
            None,
            None,
            Error(
                match_call.original_node,
                f"We do not support calls to the ``match`` function with more than "
                f"two arguments (pattern and the text to be matched) "
                f"since we could not transpile to other languages and schemas "
                f"(*e.g.*, flags such as multi-line matching)"
            )
        )

    # noinspection PyUnresolvedReferences
    if not (
            isinstance(match_call.args[1], parse_tree.Name)
            and match_call.args[1].identifier != parsed.arguments[0].name
    ):
        return (
            None,
            None,
            Error(
                match_call.original_node,
                f"The second argument, the text to be matched, to ``match`` "
                f"needs to correspond to the single argument of "
                f"the verification ""function, {parsed.arguments[0].name!r}. "
                "Otherwise, we can not transpile the pattern to schemas."
            )
        )

    for i, stmt in enumerate(parsed.body):

    print(f"match_call is: {parse_tree.dump(match_call)}")  # TODO: debug
    raise NotImplementedError()
    # TODO: implement this till the end once we understand the pattern matching statements in _rules
