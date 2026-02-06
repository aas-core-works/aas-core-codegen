"""Generate the test code for the ``over_X_or_empty`` methods."""

import io
from typing import List, Optional

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


def _generate_test_case(cls: intermediate.ConcreteClass) -> Optional[Stripped]:
    """
    Generate the test case class for the given ``cls``.

    If there are no ``over_X_or_empty`` methods, return None.
    """
    xml_cls_name = naming.xml_class_name(cls.name)

    python_cls_name = python_naming.class_name(cls.name)

    test_methods = []  # type: List[Stripped]

    for prop in cls.properties:
        if not (
            isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
            and isinstance(prop.type_annotation.value, intermediate.ListTypeAnnotation)
        ):
            continue

        over_x_or_empty_name = python_naming.method_name(
            Identifier(f"over_{prop.name}_or_empty")
        )

        test_case_method_name = python_naming.method_name(
            Identifier(f"test_{over_x_or_empty_name}_against_recorded")
        )

        file_name = f"{over_x_or_empty_name}.trace"

        test_methods.append(
            Stripped(
                f"""\
def {test_case_method_name}(self) -> None:
{I}for minimal_or_maximal in ["minimal", "maximal"]:
{II}instance = tests.common_xmlization.must_load(
{III}pathlib.Path(
{IIII}tests.common.TEST_DATA_DIR
{IIII}/ "Xml"
{IIII}/ "Expected"
{IIII}/ {xml_cls_name!r}
{IIII}/ f"{{minimal_or_maximal}}.xml"
{III})
{II})

{II}assert isinstance(
{III}instance,
{III}aas_types.{python_cls_name}
{II})

{II}log = [
{III}tests.common.trace(
{IIII}list(instance.{over_x_or_empty_name}())
{III})
{II}]

{II}got_text = tests.common.trace_log_as_text_file_content(log)

{II}expected_path = pathlib.Path(
{III}tests.common.TEST_DATA_DIR
{III}/ "test_over_X_or_empty"
{III}/ {xml_cls_name!r}
{III}/ f"on_{{minimal_or_maximal}}.xml"
{III}/ {file_name!r}
{II})

{II}tests.common.record_or_check(expected_path, got_text)"""
            )
        )

    if len(test_methods) == 0:
        return None

    test_class_name = python_naming.class_name(Identifier(f"Test_{cls.name}"))

    body = "\n\n".join(test_methods)

    return Stripped(
        f"""\
class {test_class_name}(unittest.TestCase):
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
    Generate the test code for the ``over_X_or_empty`` methods.

    The ``aas_module`` indicates the fully-qualified name of the base module.
    """
    blocks = [
        Stripped(
            '''\
"""Test ``over_X_or_empty`` methods."""'''
        ),
        python_common.WARNING,
        Stripped(
            """\
# pylint: disable=missing-docstring"""
        ),
        Stripped(
            """\
import pathlib
import unittest"""
        ),
        Stripped(
            f"""\
import {aas_module}.types as aas_types"""
        ),
        Stripped(
            """\
import tests.common_xmlization"""
        ),
    ]

    for cls in symbol_table.concrete_classes:
        test_case = _generate_test_case(cls=cls)

        if test_case is None:
            continue

        blocks.append(test_case)

    blocks.extend(
        [
            Stripped(
                f"""\
if __name__ == "__main__":
{I}unittest.main()"""
            ),
            python_common.WARNING,
        ]
    )

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue()
