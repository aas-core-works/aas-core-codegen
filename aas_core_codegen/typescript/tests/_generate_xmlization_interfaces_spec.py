"""Generate code to test the XML de/serialization of interfaces."""

import io
from typing import List

from icontract import ensure

from aas_core_codegen import intermediate
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
    """Generate code to test the XML de/serialization of interfaces."""
    blocks = [
        Stripped(
            """\
/**
 * Test XML de/serialization of interfaces.
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

    for cls in symbol_table.classes:
        if cls.interface is None or len(cls.interface.implementers) == 0:
            continue

        interface_name_typescript = typescript_naming.interface_name(cls.name)
        as_function = typescript_naming.function_name(Identifier(f"as_{cls.name}"))

        for implementer_cls in cls.interface.implementers:
            if (
                implementer_cls.serialization is None
                or not implementer_cls.serialization.with_model_type
            ):
                continue

            cls_name_typescript = typescript_naming.class_name(implementer_cls.name)
            load_minimal_name = typescript_naming.function_name(
                Identifier(f"load_minimal_{implementer_cls.name}")
            )

            blocks.append(
                Stripped(
                    f"""\
test(
{I}"{interface_name_typescript} XML round-trip " +
{I}"starting from {cls_name_typescript} OK",
{I}() => {{
{II}const instance = TestCommonXmlization.{load_minimal_name}();

{II}const xmlText = AasXmlization.toXmlString(instance);
{II}const anotherInstanceOrError = AasXmlization.fromXmlString(xmlText);
{II}expect(anotherInstanceOrError.error).toBeNull();
{II}const anotherInstance = anotherInstanceOrError.mustValue();

{II}const asInterface = AasTypes.{as_function}(anotherInstance);
{II}expect(asInterface).not.toBeNull();
{I}}}
);"""
                )
            )

        blocks.append(
            Stripped(
                f"""\
test("{interface_name_typescript} XML deserialization fail", () => {{
{I}const instanceOrError = AasXmlization.fromXmlString("This is not XML.");
{I}expect(instanceOrError.error).not.toBeNull();
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
