"""Generate the test code for the xmlization errors."""

from typing import List

from icontract import ensure

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import Stripped, indent_but_first_line, Identifier
from aas_core_codegen.csharp import common as csharp_common, naming as csharp_naming
from aas_core_codegen.csharp.common import (
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
def generate(
    namespace: csharp_common.NamespaceIdentifier,
    symbol_table: intermediate.SymbolTable,
) -> str:
    """
    Generate the test code for the xmlization errors.

    The ``namespace`` indicates the fully-qualified name of the base project.
    """
    if len(symbol_table.concrete_classes) == 0:
        raise ValueError(
            "Expected at least one concrete class in the symbol table, but got none."
        )

    concrete_cls = symbol_table.concrete_classes[0]

    cls_name_xml = naming.xml_class_name(concrete_cls.name)

    from_name = csharp_naming.method_name(Identifier(f"{concrete_cls.name}_from"))

    cls_name_csharp = csharp_naming.class_name(concrete_cls.name)

    blocks = [
        Stripped(
            f"""\
[Test]
public void Test_error_on_unexpected_declaration()
{{
{I}string path = Path.Combine(
{II}Aas.Tests.Common.TestDataDir,
{II}"Xml",
{II}"Expected",
{II}{csharp_common.string_literal(cls_name_xml)},
{II}"minimal.xml");

{I}var text = System.IO.File.ReadAllText(path, System.Text.Encoding.UTF8);

{I}// We assume no XML declarations in our test data.
{I}if (!text.StartsWith("<{cls_name_xml} "))
{I}{{
{II}throw new System.InvalidOperationException(
{III}"We expect our test example in XML to start with '<{cls_name_xml} ', "
{IIII}+ $"but it does not: {{path}}"
{II});
{I}}}

{I}text = (
{II}"<?xml version=\\"1.0\\" encoding=\\"utf-8\\"?>"
{III}+ text
{I});

{I}using var stringReader = new System.IO.StringReader(
{II}text);

{I}using var xmlReader = System.Xml.XmlReader.Create(
{II}stringReader);

{I}// We intentionally do not call `MoveToContent` to test the error message.
{I}// This is a very common situation, see:
{I}// https://github.com/aas-core-works/aas-core3.0-csharp/issues/24

{I}string? message = null;

{I}try
{I}{{
{II}Aas.Xmlization.Deserialize.{from_name}(
{III}xmlReader);
{I}}}
{I}catch (Aas.Xmlization.Exception exception)
{I}{{
{II}message = exception.Message;
{I}}}

{I}if (message == null)
{I}{{
{II}throw new AssertionException("Unexpected no exception");
{I}}}
{I}Assert.AreEqual(
{II}"Unexpected XML declaration when reading an instance of " +
{II}"class {cls_name_csharp}, as we expect the reader to be set at content " +
{II}"with MoveToContent at: the beginning",
{II}message);
}}"""
        ),
    ]  # type: List[Stripped]

    blocks_joined = "\n\n".join(blocks)

    return f"""\
{csharp_common.WARNING}

using Aas = {namespace};  // renamed

using Path = System.IO.Path;

using NUnit.Framework; // can't alias

namespace {namespace}.Tests
{{
{I}public class TestXmlizationErrors
{I}{{
{II}{indent_but_first_line(blocks_joined, II)}
{I}}}  // class TestXmlizationErrors
}}  // namespace {namespace}.Tests

{csharp_common.WARNING}
"""


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
