"""Generate code to test the XML de/serialization of concrete classes."""

import io
from typing import List

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
    INDENT3 as III,
    INDENT4 as IIII,
)


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable) -> str:
    """Generate code to test the XML de/serialization of concrete classes."""
    blocks = [
        Stripped(
            """\
/**
 * Test XML de/serialization of concrete classes.
 */"""
        ),
        typescript_common.WARNING,
        Stripped(
            """\
import * as fs from "fs";
import * as path from "path";

import * as AasXmlization from "../src/xmlization";
import * as AasTypes from "../src/types";
import * as AasVerification from "../src/verification";

import * as TestCommon from "./common";"""
        ),
    ]  # type: List[Stripped]

    for concrete_cls in symbol_table.concrete_classes:
        cls_name_typescript = typescript_naming.class_name(concrete_cls.name)
        cls_name_xml = naming.xml_class_name(concrete_cls.name)
        as_function = typescript_naming.function_name(
            Identifier(f"as_{concrete_cls.name}")
        )

        blocks.append(
            Stripped(
                f"""\
test("{cls_name_typescript} XML round-trip OK", () => {{
{I}const pths = Array.from(
{II}TestCommon.findFilesBySuffixRecursively(
{III}path.join(
{IIII}TestCommon.TEST_DATA_DIR,
{IIII}"Xml",
{IIII}"Expected",
{IIII}{typescript_common.string_literal(cls_name_xml)}
{III}),
{III}".xml"
{II})
{I});
{I}pths.sort();

{I}for (const pth of pths) {{
{II}const text = fs.readFileSync(pth, "utf-8");

{II}const instanceOrError = AasXmlization.fromXmlString(text);
{II}expect(instanceOrError.error).toBeNull();
{II}const instance = instanceOrError.mustValue();

{II}const casted = AasTypes.{as_function}(instance);
{II}if (casted === null) {{
{III}throw new Error(
{IIII}`Expected instance of {cls_name_typescript} in ${{pth}}, ` +
{IIII}`but got: ${{typeof instance}}`
{III});
{II}}}

{II}TestCommon.assertNoVerificationErrors(AasVerification.verify(casted), pth);

{II}const roundTripText = AasXmlization.toXmlString(casted);
{II}expect(roundTripText.length).toBeGreaterThan(0);
{I}}}
}});"""
            )
        )

        blocks.append(
            Stripped(
                f"""\
test("{cls_name_typescript} XML deserialization fail", () => {{
{I}for (
{II}const causeDir of
{II}TestCommon.findImmediateSubdirectories(
{III}path.join(
{IIII}TestCommon.TEST_DATA_DIR,
{IIII}"Xml",
{IIII}"Unexpected",
{IIII}"Unserializable"
{III})
{II})
{I}) {{
{II}const clsDir = path.join(
{III}causeDir,
{III}{typescript_common.string_literal(cls_name_xml)}
{II});
{II}if (!fs.existsSync(clsDir)) {{
{III}continue;
{II}}}

{II}const pths = Array.from(
{III}TestCommon.findFilesBySuffixRecursively(
{IIII}clsDir,
{IIII}".xml"
{III})
{II});
{II}pths.sort();

{II}for (const pth of pths) {{
{III}const text = fs.readFileSync(pth, "utf-8");
{III}const instanceOrError = AasXmlization.fromXmlString(text);
{III}expect(instanceOrError.error).not.toBeNull();
{II}}}
{I}}}
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
