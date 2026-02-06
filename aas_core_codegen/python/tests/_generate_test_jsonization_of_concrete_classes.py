"""Generate the code to test JSON de/serialization of concrete classes."""

import io
from typing import List

from icontract import ensure

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import Stripped, Identifier, indent_but_first_line
from aas_core_codegen.python import common as python_common, naming as python_naming
from aas_core_codegen.python.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
)


def _generate_test_case(symbol_table: intermediate.SymbolTable) -> Stripped:
    test_methods = []  # type: List[Stripped]

    for cls in symbol_table.concrete_classes:
        test_method_name = python_naming.method_name(Identifier(f"test_{cls.name}"))

        from_jsonable = python_naming.function_name(
            Identifier(f"{cls.name}_from_jsonable")
        )

        model_type = naming.json_model_type(cls.name)

        test_methods.append(
            Stripped(
                f"""\
def {test_method_name}(self) -> None:
{I}for path in sorted(
{II}(
{III}tests.common.TEST_DATA_DIR
{III}/ "Json"
{III}/ "Expected"
{III}/ {model_type!r}
{II}).glob("**/*.json")
{I}):
{II}with path.open("rt") as fid:
{III}original_jsonable = json.load(fid)

{II}instance = aas_jsonization.{from_jsonable}(
{III}original_jsonable
{II})

{II}another_jsonable = aas_jsonization.to_jsonable(instance)

{II}mismatches = tests.common_jsonization.check_equal(
{III}original_jsonable,
{III}another_jsonable
{II})
{II}self.assertListEqual([], list(map(str, mismatches)))"""
            ),
        )

    body = (
        "\n\n".join(test_methods)
        if len(test_methods) > 0
        else """\
# There are no concrete classes.
pass"""
    )

    return Stripped(
        f"""\
class TestRoundTrips(unittest.TestCase):
{I}{indent_but_first_line(body, I)}"""
    )


@ensure(
    lambda result: result.endswith("\n"),
    "Trailing newline mandatory for valid end-of-files",
)
def generate(
    symbol_table: intermediate.SymbolTable,
    aas_module: python_common.QualifiedModuleName,
) -> str:
    """
    Generate the code to test JSON de/serialization of concrete classes.

    The ``aas_module`` indicates the fully-qualified name of the base module.
    """
    blocks = [
        Stripped(
            '''\
"""Test JSON de/serialization of concrete classes."""'''
        ),
        python_common.WARNING,
        Stripped(
            """\
# pylint: disable=missing-docstring"""
        ),
        Stripped(
            """\
import json
import unittest"""
        ),
        Stripped(
            f"""\
import {aas_module}.jsonization as aas_jsonization"""
        ),
        Stripped(
            """\
import tests.common_jsonization"""
        ),
        _generate_test_case(symbol_table=symbol_table),
        Stripped(
            f"""\
if __name__ == "__main__":
{I}unittest.main()"""
        ),
        python_common.WARNING,
    ]

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue()
