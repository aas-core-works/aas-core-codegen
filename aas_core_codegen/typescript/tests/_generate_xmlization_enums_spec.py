"""Generate code to test the XML de/serialization of enumerations."""

import io
from typing import List, Optional

from icontract import ensure

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import Stripped, Identifier
from aas_core_codegen.typescript import (
    common as typescript_common,
    naming as typescript_naming,
)
from aas_core_codegen.typescript.common import (
    INDENT as I,
    INDENT2 as II,
)


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable) -> str:
    """Generate code to test the XML de/serialization of enumerations."""
    blocks = [
        Stripped(
            """\
/**
 * Test XML de/serialization of enumeration literals.
 */"""
        ),
        typescript_common.WARNING,
        Stripped(
            """\
import * as AasXmlization from "../src/xmlization";
import * as AasTypes from "../src/types";

import * as TestCommonXmlization from "./commonXmlization";"""
        ),
    ]  # type: List[Stripped]

    for enumeration in symbol_table.enumerations:
        enum_name_typescript = typescript_naming.enum_name(enumeration.name)

        carrier_cls = None  # type: Optional[intermediate.ConcreteClass]
        carrier_prop = None  # type: Optional[intermediate.Property]
        for cls in symbol_table.concrete_classes:
            for prop in cls.properties:
                type_anno = intermediate.beneath_optional(prop.type_annotation)
                if not isinstance(type_anno, intermediate.OurTypeAnnotation):
                    continue

                if type_anno.our_type is enumeration:
                    carrier_cls = cls
                    carrier_prop = prop
                    break

            if carrier_cls is not None:
                break

        if carrier_cls is None or carrier_prop is None:
            raise AssertionError(
                f"Expected an enum carrier property for XML round-trip tests, "
                f"but found none for: {enumeration.name}"
            )

        cls_name_typescript = typescript_naming.class_name(carrier_cls.name)
        prop_name_typescript = typescript_naming.property_name(carrier_prop.name)
        load_maximal_name = typescript_naming.function_name(
            Identifier(f"load_maximal_{carrier_cls.name}")
        )
        as_function = typescript_naming.function_name(
            Identifier(f"as_{carrier_cls.name}")
        )

        blocks.append(
            Stripped(
                f"""\
test("{enum_name_typescript} XML round-trip OK", () => {{
{I}const instance = TestCommonXmlization.{load_maximal_name}();

{I}const xmlText = AasXmlization.toXmlString(instance);
{I}const anotherOrError = AasXmlization.fromXmlString(xmlText);
{I}expect(anotherOrError.error).toBeNull();

{I}const casted = AasTypes.{as_function}(anotherOrError.mustValue());
{I}expect(casted).not.toBeNull();
{I}expect(casted.{prop_name_typescript}).toStrictEqual(
{II}instance.{prop_name_typescript}
{I});
}});"""
            )
        )

        literal_value_set = set(literal.value for literal in enumeration.literals)
        invalid_literal_value = "invalid-literal"
        while invalid_literal_value in literal_value_set:
            invalid_literal_value = f"very-{invalid_literal_value}"

        prop_xml_name_literal = typescript_common.string_literal(
            naming.xml_property(carrier_prop.name)
        )
        invalid_literal_literal = typescript_common.string_literal(invalid_literal_value)

        blocks.append(
            Stripped(
                f"""\
test("{enum_name_typescript} XML deserialization fail", () => {{
{I}const instance = TestCommonXmlization.{load_maximal_name}();
{I}const xmlText = AasXmlization.toXmlString(instance);

{I}const regex = new RegExp(
{II}`(<${{{prop_xml_name_literal}}}>)([^<]*)(</${{{prop_xml_name_literal}}}>)`
{I});
{I}const brokenXmlText = xmlText.replace(
{II}regex,
{II}`$1${{{invalid_literal_literal}}}$3`
{I});

{I}expect(brokenXmlText).not.toStrictEqual(xmlText);

{I}const anotherOrError = AasXmlization.fromXmlString(brokenXmlText);
{I}expect(anotherOrError.error).not.toBeNull();
}});"""
            )
        )

    blocks.append(typescript_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
