"""Generate the code to test XML de/serialization of concrete classes."""

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
    INDENT4 as IIII,
)


def _generate_test_case(symbol_table: intermediate.SymbolTable) -> Stripped:
    test_methods = []  # type: List[Stripped]

    for cls in symbol_table.concrete_classes:
        xml_class_name = naming.xml_class_name(cls.name)

        test_method_name = python_naming.method_name(Identifier(f"test_{cls.name}"))

        from_iterparse = python_naming.function_name(
            Identifier(f"{cls.name}_from_iterparse")
        )

        from_stream = python_naming.function_name(Identifier(f"{cls.name}_from_stream"))

        from_file = python_naming.function_name(Identifier(f"{cls.name}_from_file"))

        from_str = python_naming.function_name(Identifier(f"{cls.name}_from_str"))

        test_methods.append(
            Stripped(
                f"""\
def {test_method_name}(self) -> None:
{I}for path in sorted(
{II}(
{III}tests.common.TEST_DATA_DIR
{III}/ "Xml"
{III}/ "Expected"
{III}/ {xml_class_name!r}
{II}).glob("**/*.xml")
{I}):
{II}text = path.read_text(encoding="utf-8")
{II}et_concrete = ET.fromstring(text)
{II}tests.common_xmlization.remove_redundant_whitespace(et_concrete)

{II}# region From iterparse
{II}iterator = ET.iterparse(source=io.StringIO(text), events=["start", "end"])
{II}got_from_iterparse = (
{III}aas_xmlization.{from_iterparse}(iterator)
{II})

{II}et_from_iterparse = ET.fromstring(aas_xmlization.to_str(got_from_iterparse))
{II}tests.common_xmlization.remove_redundant_whitespace(et_from_iterparse)
{II}tests.common_xmlization.assert_elements_equal(et_concrete, et_from_iterparse)
{II}# endregion

{II}# region From stream
{II}got_from_stream = (
{III}aas_xmlization
{III}.{from_stream}(
{IIII}io.StringIO(text)
{III})
{II})
{II}et_from_stream = ET.fromstring(aas_xmlization.to_str(got_from_stream))
{II}tests.common_xmlization.remove_redundant_whitespace(et_from_stream)
{II}tests.common_xmlization.assert_elements_equal(et_concrete, et_from_stream)
{II}# endregion

{II}# region From file
{II}with tempfile.TemporaryDirectory() as tmp_dir:
{III}path = pathlib.Path(tmp_dir) / "something.xml"
{III}path.write_text(text, encoding="utf-8")

{III}got_from_file = (
{IIII}aas_xmlization
{IIII}.{from_file}(path)
{III})
{II}et_from_file = ET.fromstring(aas_xmlization.to_str(got_from_file))
{II}tests.common_xmlization.remove_redundant_whitespace(et_from_file)
{II}tests.common_xmlization.assert_elements_equal(et_concrete, et_from_file)
{II}# endregion

{II}# region From string
{II}got_from_str = (
{III}aas_xmlization
{III}.{from_str}(text)
{II})
{II}et_from_str = ET.fromstring(aas_xmlization.to_str(got_from_str))
{II}tests.common_xmlization.remove_redundant_whitespace(et_from_str)
{II}tests.common_xmlization.assert_elements_equal(et_concrete, et_from_str)
{II}# endregion"""
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
    Generate the code to test XML de/serialization of concrete classes.

    The ``aas_module`` indicates the fully-qualified name of the base module.
    """
    blocks = [
        Stripped(
            '''\
"""Test XML de/serialization of concrete classes."""'''
        ),
        python_common.WARNING,
        Stripped(
            """\
# pylint: disable=missing-docstring"""
        ),
        Stripped(
            """\
import io
import pathlib
import tempfile
import unittest
import xml.etree.ElementTree as ET"""
        ),
        Stripped(
            f"""\
import {aas_module}.xmlization as aas_xmlization"""
        ),
        Stripped(
            """\
import tests.common_xmlization"""
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
