"""Generate code for targeted negative XMLization tests."""

import io
from typing import List, Optional, Tuple

from icontract import ensure

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import Stripped
from aas_core_codegen.typescript import common as typescript_common
from aas_core_codegen.typescript.common import INDENT as I


def _first_concrete_class(
    symbol_table: intermediate.SymbolTable,
) -> Optional[intermediate.ConcreteClass]:
    """Select the first concrete class, if any."""
    for concrete_cls in symbol_table.concrete_classes:
        return concrete_cls

    return None


def _first_property_for_duplicate_check(
    cls: intermediate.ConcreteClass,
) -> Optional[intermediate.Property]:
    """Select a property to test duplicate-property parsing checks."""
    required_candidate = None  # type: Optional[intermediate.Property]
    any_candidate = None  # type: Optional[intermediate.Property]

    for prop in cls.properties:
        if any_candidate is None:
            any_candidate = prop

        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            required_candidate = prop
            break

    if required_candidate is not None:
        return required_candidate

    return any_candidate


def _first_atomic_list_property_candidate(
    symbol_table: intermediate.SymbolTable,
) -> Optional[Tuple[intermediate.ConcreteClass, intermediate.Property]]:
    """Find a class with a list property whose XML items should be tagged as ``v``."""
    for concrete_cls in symbol_table.concrete_classes:
        for prop in concrete_cls.properties:
            type_anno = intermediate.beneath_optional(prop.type_annotation)
            if not isinstance(type_anno, intermediate.ListTypeAnnotation):
                continue

            items = type_anno.items
            if not isinstance(
                items,
                (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
            ):
                continue

            if isinstance(items, intermediate.OurTypeAnnotation) and isinstance(
                items.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            ):
                continue

            return concrete_cls, prop

    return None


def _first_nested_class_dispatch_candidate(
    symbol_table: intermediate.SymbolTable,
) -> Optional[Tuple[intermediate.ConcreteClass, intermediate.Property]]:
    """Find a property parsed through ``parsePropertyAsClassInstance``."""
    for concrete_cls in symbol_table.concrete_classes:
        for prop in concrete_cls.properties:
            type_anno = intermediate.beneath_optional(prop.type_annotation)
            if not isinstance(type_anno, intermediate.OurTypeAnnotation):
                continue

            if not isinstance(
                type_anno.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            ):
                continue

            if (
                isinstance(type_anno.our_type, intermediate.ConcreteClass)
                and len(type_anno.our_type.concrete_descendants) == 0
            ):
                continue

            return concrete_cls, prop

    return None


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable) -> str:
    """Generate code for targeted negative XMLization tests."""
    blocks = [
        Stripped(
            """\
/**
 * Test failure modes in XML parsing to exercise defensive branches.
 */"""
        ),
        typescript_common.WARNING,
        Stripped(
            """\
import * as fs from "fs";
import * as path from "path";

import * as AasXmlization from "../src/xmlization";

import * as TestCommon from "./common";

function readExpectedXml(classXmlName: string, fileName: "minimal.xml" | "maximal.xml"): string {
  const pth = path.join(TestCommon.TEST_DATA_DIR, "Xml", "Expected", classXmlName, fileName);
  return fs.readFileSync(pth, "utf-8");
}

function expectDeserializationError(xmlText: string): void {
  const instanceOrError = AasXmlization.fromXmlString(xmlText);
  expect(instanceOrError.error).not.toBeNull();
}

function escapeRegExp(text: string): string {
    return text.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&");
}"""
        ),
    ]  # type: List[Stripped]

    first_cls = _first_concrete_class(symbol_table)
    if first_cls is not None:
        first_cls_xml_name = naming.xml_class_name(first_cls.name)
        first_cls_xml_name_literal = typescript_common.string_literal(
            first_cls_xml_name
        )

        blocks.append(
            Stripped(
                f"""\
test("XML namespace mismatch fails", () => {{
{I}const text = readExpectedXml({first_cls_xml_name_literal}, "minimal.xml");
{I}const brokenText = text.replace(
{I}{I}/xmlns=\"[^\"]*\"/,
{I}{I}'xmlns="urn:aas-core-codegen:broken"'
{I});

{I}expect(brokenText).not.toStrictEqual(text);
{I}expectDeserializationError(brokenText);
}});"""
            )
        )

        blocks.append(
            Stripped(
                f"""\
test("XML wrong root closing element fails", () => {{
{I}const text = readExpectedXml({first_cls_xml_name_literal}, "minimal.xml");
{I}const expectedClosing = "</{first_cls_xml_name}>";
{I}const insertionIndex = text.lastIndexOf(expectedClosing);
{I}if (insertionIndex < 0) {{
{I}{I}throw new Error(`Failed to find root closing tag: ${{expectedClosing}}`);
{I}}}

{I}const brokenClosing = "</{first_cls_xml_name}_BROKEN>";
{I}const brokenText =
{I}{I}text.slice(0, insertionIndex) +
{I}{I}brokenClosing +
{I}{I}text.slice(insertionIndex + expectedClosing.length);

{I}expectDeserializationError(brokenText);
}});"""
            )
        )

        duplicate_prop = _first_property_for_duplicate_check(first_cls)
        if duplicate_prop is not None:
            duplicate_prop_xml_name = naming.xml_property(duplicate_prop.name)
            duplicate_prop_xml_literal = typescript_common.string_literal(
                duplicate_prop_xml_name
            )
            duplicate_file_name = (
                "minimal.xml"
                if not isinstance(
                    duplicate_prop.type_annotation,
                    intermediate.OptionalTypeAnnotation,
                )
                else "maximal.xml"
            )

            blocks.append(
                Stripped(
                    f"""\
test("XML duplicate property fails", () => {{
{I}const text = readExpectedXml({first_cls_xml_name_literal}, {typescript_common.string_literal(duplicate_file_name)});

{I}const propertyName = {duplicate_prop_xml_literal};
{I}const propertyPattern = new RegExp(
{I}{I}`(<${{escapeRegExp(propertyName)}}>[\\\\s\\\\S]*?</${{escapeRegExp(propertyName)}}>)`
{I});
{I}const match = propertyPattern.exec(text);
{I}if (match === null) {{
{I}{I}throw new Error(`Failed to find a property element for: ${{propertyName}}`);
{I}}}

{I}const rootClosing = "</{first_cls_xml_name}>";
{I}const insertionIndex = text.lastIndexOf(rootClosing);
{I}if (insertionIndex < 0) {{
{I}{I}throw new Error(`Failed to find root closing tag: ${{rootClosing}}`);
{I}}}

{I}const duplicatedProperty = match[1];
{I}const brokenText =
{I}{I}text.slice(0, insertionIndex) +
{I}{I}duplicatedProperty +
{I}{I}text.slice(insertionIndex);

{I}expectDeserializationError(brokenText);
}});"""
                )
            )

    atomic_list_candidate = _first_atomic_list_property_candidate(symbol_table)
    if atomic_list_candidate is not None:
        list_cls, list_prop = atomic_list_candidate
        list_cls_xml_name = naming.xml_class_name(list_cls.name)
        list_cls_xml_name_literal = typescript_common.string_literal(list_cls_xml_name)
        list_prop_xml_name_literal = typescript_common.string_literal(
            naming.xml_property(list_prop.name)
        )

        blocks.append(
            Stripped(
                f"""\
test("XML list item element name mismatch fails", () => {{
{I}const text = readExpectedXml({list_cls_xml_name_literal}, "maximal.xml");

{I}const propertyName = {list_prop_xml_name_literal};
{I}const propertyPattern = new RegExp(
{I}{I}`(<${{escapeRegExp(propertyName)}}>[\\\\s\\\\S]*?</${{escapeRegExp(propertyName)}}>)`
{I});
{I}const match = propertyPattern.exec(text);
{I}if (match === null) {{
{I}{I}throw new Error(`Failed to find a list property element for: ${{propertyName}}`);
{I}}}

{I}const brokenProperty =
{I}{I}match[1]
{I}{I}{I}.replace("<v>", "<invalidListItem>")
{I}{I}{I}.replace("</v>", "</invalidListItem>");

{I}expect(brokenProperty).not.toStrictEqual(match[1]);

{I}const brokenText = text.replace(match[1], brokenProperty);
{I}expectDeserializationError(brokenText);
}});"""
            )
        )

    nested_dispatch_candidate = _first_nested_class_dispatch_candidate(symbol_table)
    if nested_dispatch_candidate is not None:
        nested_cls, nested_prop = nested_dispatch_candidate
        nested_cls_xml_name = naming.xml_class_name(nested_cls.name)
        nested_cls_xml_name_literal = typescript_common.string_literal(
            nested_cls_xml_name
        )
        nested_prop_xml_name_literal = typescript_common.string_literal(
            naming.xml_property(nested_prop.name)
        )

        blocks.append(
            Stripped(
                f"""\
test("XML nested class dispatch mismatch fails", () => {{
{I}const text = readExpectedXml({nested_cls_xml_name_literal}, "maximal.xml");

{I}const propertyName = {nested_prop_xml_name_literal};
{I}const propertyPattern = new RegExp(
{I}{I}`(<${{escapeRegExp(propertyName)}}>\\\\s*)` +
{I}{I}`(<([A-Za-z_][\\\\w.-]*)>)` +
{I}{I}`([\\\\s\\\\S]*?)(</\\\\3>)` +
{I}{I}`(\\\\s*</${{escapeRegExp(propertyName)}}>)`
{I});
{I}const match = propertyPattern.exec(text);
{I}if (match === null) {{
{I}{I}throw new Error(`Failed to find a nested class in property: ${{propertyName}}`);
{I}}}

{I}const brokenProperty =
{I}{I}`${{match[1]}}<UnknownNestedClassXmlElement>${{match[4]}}` +
{I}{I}`</UnknownNestedClassXmlElement>${{match[6]}}`;

{I}const brokenText = text.replace(match[0], brokenProperty);
{I}expectDeserializationError(brokenText);
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
assert __doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
