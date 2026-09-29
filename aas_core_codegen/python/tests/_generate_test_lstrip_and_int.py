"""Generate the unit tests for ``str.lstrip`` and ``int`` on strings."""

from typing import List

from icontract import ensure, require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped, indent_but_first_line
from aas_core_codegen.python import common as python_common
from aas_core_codegen.python.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
)


# fmt: off
@require(
    lambda symbol_table:
    intermediate.uses_lstrip(symbol_table) or intermediate.uses_int(symbol_table)
)
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable,
    qualified_module_name: python_common.QualifiedModuleName,
) -> str:
    """
    Generate the unit tests for ``str.lstrip`` and ``int`` on strings.

    The Python SDK uses the native ``str.lstrip``, which serves as the reference for
    the other SDKs. The built-in ``int`` is transpiled to ``parse_safe_int``, which
    is stricter than the native ``int``, so that all the SDKs behave the same. We
    generate the tests from the very same cases in all the SDKs, see
    :py:mod:`aas_core_codegen.tests_common`.

    The ``qualified_module_name`` indicates the fully-qualified name of the base
    module.
    """
    methods = []  # type: List[Stripped]

    if intermediate.uses_lstrip(symbol_table):
        for i, (text, chars, expected) in enumerate(tests_common.LSTRIP_CASES):
            methods.append(
                Stripped(
                    f"""\
def test_lstrip_{i}(self) -> None:
{I}self.assertEqual(
{II}{python_common.string_literal(expected)},
{II}{python_common.string_literal(text)}.lstrip(
{III}{python_common.string_literal(chars)}
{II})
{I})"""
                )
            )

    if intermediate.uses_int(symbol_table):
        for i, (text, expected_int) in enumerate(tests_common.PARSE_INT_CASES):
            methods.append(
                Stripped(
                    f"""\
def test_int_{i}(self) -> None:
{I}self.assertEqual(
{II}{expected_int},
{II}aas_common.parse_safe_int({python_common.string_literal(text)})
{I})"""
                )
            )

        for i, text in enumerate(tests_common.PARSE_INT_INVALID_CASES):
            methods.append(
                Stripped(
                    f"""\
def test_int_invalid_{i}(self) -> None:
{I}with self.assertRaises(ValueError):
{II}aas_common.parse_safe_int({python_common.string_literal(text)})"""
                )
            )

    methods_joined = "\n\n".join(methods)

    if intermediate.uses_int(symbol_table):
        imports = Stripped(
            f"""\
import unittest

import {qualified_module_name}.common as aas_common"""
        )
    else:
        imports = Stripped("import unittest")

    blocks = [
        Stripped(
            '''\
"""
Test ``str.lstrip`` and ``int`` on strings as used in the transpiled code.

The transpiled ``str.lstrip`` follows the Python implementation, since Python is
the language of the meta-model specifications. Hence, it strips the characters
(code points).

The built-in ``int`` is transpiled to ``parse_safe_int``, which is stricter than
the Python ``int``. It accepts only an optional sign followed by the ASCII digits,
and only the safe integers, *i.e.*, the integers within ``-(2 ** 53 - 1)`` and
``2 ** 53 - 1``. Otherwise, it raises.

The other SDKs test against the very same cases.
"""'''
        ),
        python_common.WARNING,
        Stripped(
            """\
# pylint: disable=missing-docstring"""
        ),
        imports,
        Stripped(
            f"""\
class Test_lstrip_and_int(unittest.TestCase):
{I}{indent_but_first_line(methods_joined, I)}"""
        ),
        Stripped(
            f"""\
if __name__ == "__main__":
{I}unittest.main()"""
        ),
        python_common.WARNING,
    ]

    return "\n\n\n".join(blocks) + "\n"


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
