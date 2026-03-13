"""Generate code to test the XML de/serialization of concrete classes."""

from typing import List

from icontract import ensure

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import Stripped, indent_but_first_line
from aas_core_codegen.csharp import common as csharp_common, naming as csharp_naming
from aas_core_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
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
    Generate code to test the XML de/serialization of concrete classes.

    The ``namespace`` indicates the fully-qualified name of the base project.
    """
    xml_namespace_literal = csharp_common.string_literal(
        symbol_table.meta_model.xml_namespace
    )

    blocks = [
        Stripped(
            f"""\
private static void CheckElementsEqual(
{I}XElement expected,
{I}XElement got,
{I}out Reporting.Error? error)
{{
{I}error = null;

{I}if (expected.Name.LocalName != got.Name.LocalName)
{I}{{
{II}error = new Reporting.Error(
{III}"Mismatch in element names: " +
{III}$"{{expected}} != {{got}}"
{II});
{II}return;
{I}}}

{I}string? expectedContent = (expected.FirstNode as XText)?.Value;
{I}string? gotContent = (got.FirstNode as XText)?.Value;

{I}if (expectedContent != gotContent)
{I}{{
{II}error = new Reporting.Error(
{III}$"Mismatch in element contents: {{expected}} != {{got}}"
{II});
{II}return;
{I}}}

{I}var expectedChildren = expected.Elements().ToList();
{I}var gotChildren = got.Elements().ToList();

{I}if (expectedChildren.Count != gotChildren.Count)
{I}{{
{II}error = new Reporting.Error(
{III}$"Mismatch in child elements: {{expected}} != {{got}}"
{II});
{II}return;
{I}}}

{I}for (int i = 0; i < expectedChildren.Count; i++)
{I}{{
{II}CheckElementsEqual(
{III}expectedChildren[i],
{III}gotChildren[i],
{III}out error);

{II}if (error != null)
{II}{{
{III}error.PrependSegment(
{IIII}new Reporting.IndexSegment(i));

{III}error.PrependSegment(
{IIII}new Reporting.NameSegment(
{IIIII}expected.Name.ToString()));
{II}}}
{I}}}
}}"""
        ),
        Stripped(
            f"""\
private static void AssertSerializeDeserializeEqualsOriginal(
{I}Aas.IClass instance, string path)
{{
{I}// Serialize
{I}var outputBuilder = new System.Text.StringBuilder();

{I}{{
{II}using var writer = System.Xml.XmlWriter.Create(
{III}outputBuilder,
{III}new System.Xml.XmlWriterSettings()
{III}{{
{IIII}Encoding = System.Text.Encoding.UTF8,
{IIII}OmitXmlDeclaration = true
{III}}}
{II});
{II}Aas.Xmlization.Serialize.To(
{III}instance,
{III}writer);
{I}}}

{I}string outputText = outputBuilder.ToString();

{I}// Compare input == output
{I}{{
{II}using var outputReader = new System.IO.StringReader(outputText);
{II}var gotDoc = XDocument.Load(outputReader);

{II}Assert.AreEqual(
{III}gotDoc.Root?.Name.Namespace.ToString(),
{III}{xml_namespace_literal});

{II}foreach (var child in gotDoc.Descendants())
{II}{{
{III}Assert.AreEqual(
{IIII}child.GetDefaultNamespace().NamespaceName,
{IIII}{xml_namespace_literal});
{II}}}

{II}var expectedDoc = XDocument.Load(path);

{II}CheckElementsEqual(
{III}expectedDoc.Root!,
{III}gotDoc.Root!,
{III}out Reporting.Error? inequalityError);

{II}if (inequalityError != null)
{II}{{
{III}Assert.Fail(
{IIII}$"The original XML from {{path}} is unequal the serialized XML: " +
{IIII}$"#/{{Reporting.GenerateRelativeXPath(inequalityError.PathSegments)}}: " +
{IIII}inequalityError.Cause
{III});
{II}}}
{I}}}
}}"""
        ),
        Stripped(
            f"""\
private static void AssertEqualsExpectedOrRerecordDeserializationException(
{I}Aas.Xmlization.Exception? exception,
{I}string path)
{{
{I}if (exception == null)
{I}{{
{II}Assert.Fail(
{III}$"Expected a Xmlization exception when de-serializing {{path}}, but got none."
{II});
{I}}}
{I}else
{I}{{
{II}string exceptionPath = path + ".exception";
{II}string got = exception.Message;
{II}if (Aas.Tests.Common.RecordMode)
{II}{{
{III}System.IO.File.WriteAllText(exceptionPath, got);
{II}}}
{II}else
{II}{{
{III}if (!System.IO.File.Exists(exceptionPath))
{III}{{
{IIII}throw new System.IO.FileNotFoundException(
{IIIII}"The file with the recorded exception does not " +
{IIIII}$"exist: {{exceptionPath}}; maybe you want to set the environment " +
{IIIII}$"variable {{Aas.Tests.Common.RecordModeEnvironmentVariableName}}?");
{III}}}

{III}string expected = System.IO.File.ReadAllText(exceptionPath);
{III}Assert.AreEqual(
{IIII}expected.Replace("\\r\\n", "\\n"),
{IIII}got.Replace("\\r\\n", "\\n"),
{IIII}$"The expected exception does not match the actual one for the file {{path}}");
{II}}}
{I}}}
}}"""
        ),
    ]  # type: List[Stripped]

    for concrete_cls in symbol_table.concrete_classes:
        cls_name_csharp = csharp_naming.class_name(concrete_cls.name)
        cls_name_xml = naming.xml_class_name(concrete_cls.name)

        blocks.append(
            Stripped(
                f"""\
[Test]
public void Test_{cls_name_csharp}_ok()
{{
{I}var paths = Directory.GetFiles(
{II}Path.Combine(
{III}Aas.Tests.Common.TestDataDir,
{III}"Xml",
{III}"Expected",
{III}{csharp_common.string_literal(cls_name_xml)}
{II}),
{II}"*.xml",
{II}System.IO.SearchOption.AllDirectories).ToList();
{I}paths.Sort();

{I}foreach (var path in paths)
{I}{{
{II}using var xmlReader = System.Xml.XmlReader.Create(path);

{II}var instance = Aas.Xmlization.Deserialize.{cls_name_csharp}From(
{III}xmlReader);

{II}var errors = Aas.Verification.Verify(instance).ToList();
{II}Aas.Tests.Common.AssertNoVerificationErrors(errors, path);

{II}AssertSerializeDeserializeEqualsOriginal(
{III}instance, path);
{I}}}
}}  // public void Test_{cls_name_csharp}_ok"""
            )
        )

        blocks.append(
            Stripped(
                f"""\
[Test]
public void Test_{cls_name_csharp}_deserialization_fail()
{{
{I}foreach (
{II}string causeDir in
{II}Directory.GetDirectories(
{III}Path.Combine(
{IIII}Aas.Tests.Common.TestDataDir,
{IIII}"Xml",
{IIII}"Unexpected",
{IIII}"Unserializable"
{III})
{II})
{I})
{I}{{
{II}string clsDir = Path.Combine(
{III}causeDir,
{III}{csharp_common.string_literal(cls_name_xml)}
{II});

{II}if (!Directory.Exists(clsDir))
{II}{{
{III}// No examples of {cls_name_csharp} for the failure cause.
{III}continue;
{II}}}

{II}var paths = Directory.GetFiles(
{III}clsDir,
{III}"*.xml",
{III}System.IO.SearchOption.AllDirectories).ToList();
{II}paths.Sort();

{II}foreach (var path in paths)
{II}{{
{III}using var xmlReader = System.Xml.XmlReader.Create(path);

{III}Aas.Xmlization.Exception? exception = null;

{III}try
{III}{{
{IIII}_ = Aas.Xmlization.Deserialize.{cls_name_csharp}From(
{IIIII}xmlReader);
{III}}}
{III}catch (Aas.Xmlization.Exception observedException)
{III}{{
{IIII}exception = observedException;
{III}}}

{III}AssertEqualsExpectedOrRerecordDeserializationException(
{IIII}exception, path);
{II}}}
{I}}}
}}  // public void Test_{cls_name_csharp}_deserialization_fail"""
            )
        )

        blocks.append(
            Stripped(
                f"""\
[Test]
public void Test_{cls_name_csharp}_verification_fail()
{{
{I}foreach (
{II}string causeDir in
{II}Directory.GetDirectories(
{III}Path.Combine(
{IIII}Aas.Tests.Common.TestDataDir,
{IIII}"Xml",
{IIII}"Unexpected",
{IIII}"Invalid"
{III})
{II})
{I})
{I}{{
{II}string clsDir = Path.Combine(
{III}causeDir,
{III}{csharp_common.string_literal(cls_name_xml)}
{II});

{II}if (!Directory.Exists(clsDir))
{II}{{
{III}// No examples of {cls_name_csharp} for the failure cause.
{III}continue;
{II}}}

{II}var paths = Directory.GetFiles(
{III}clsDir,
{III}"*.xml",
{III}System.IO.SearchOption.AllDirectories).ToList();
{II}paths.Sort();

{II}foreach (var path in paths)
{II}{{
{III}using var xmlReader = System.Xml.XmlReader.Create(path);

{III}var instance = Aas.Xmlization.Deserialize.{cls_name_csharp}From(
{IIII}xmlReader);

{III}var errors = Aas.Verification.Verify(instance).ToList();
{III}Aas.Tests.Common.AssertEqualsExpectedOrRerecordVerificationErrors(
{IIII}errors, path);
{II}}}
{I}}}
}}  // public void Test_{cls_name_csharp}_verification_fail"""
            )
        )

    blocks_joined = "\n\n".join(blocks)

    return f"""\
{csharp_common.WARNING}

using Aas = {namespace};  // renamed

using Directory = System.IO.Directory;
using Path = System.IO.Path;

using NUnit.Framework; // can't alias
using System.Linq;  // can't alias
using System.Xml.Linq; // can't alias

namespace {namespace}.Tests
{{
{I}public class TestXmlizationOfConcreteClasses
{I}{{
{II}{indent_but_first_line(blocks_joined, II)}
{I}}}  // class TestXmlizationOfConcreteClasses
}}  // namespace {namespace}.Tests

{csharp_common.WARNING}
"""


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
