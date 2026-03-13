"""Generate code to test the XML de/serialization of concrete classes."""
import io
from typing import List

from icontract import ensure

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import (
    Stripped,
)
from aas_core_codegen.cpp import common as cpp_common, naming as cpp_naming
from aas_core_codegen.cpp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
)


# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate_implementation(
    symbol_table: intermediate.SymbolTable, library_namespace: Stripped
) -> str:
    """Generate implementation to test the XML de/serialization of concrete classes."""
    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            f"""\
#include "./common.hpp"
#include "./common_xmlization.hpp"

#include <{include_prefix_path}/xmlization.hpp>

#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>

namespace aas = {library_namespace};"""
        ),
        Stripped(
            f"""\
void AssertRoundTrip(
{I}const std::filesystem::path& path
) {{
{I}std::shared_ptr<
{II}aas::types::IClass
{I}> deserialized(
{II}test::common::xmlization::MustDeserializeFile(path)
{I});

{I}std::stringstream ss;
{I}aas::xmlization::Serialize(*deserialized, {{}}, ss);

{I}std::string expected_xml = test::common::MustReadString(path);

{I}INFO(aas::common::Concat("XML round-trip on ", path.string()))
{I}REQUIRE(
{II}test::common::xmlization::CanonicalizeXml(expected_xml)
{III}== test::common::xmlization::CanonicalizeXml(ss.str())
{I});
}}"""
        ),
        Stripped(
            f"""\
void AssertDeserializationFailure(
{I}const std::filesystem::path& path,
{I}const std::filesystem::path& error_path
) {{
{I}std::ifstream ifs(path, std::ios::binary);

{I}aas::common::expected<
{II}std::shared_ptr<aas::types::IClass>,
{II}aas::xmlization::DeserializationError
{I}> deserialized = aas::xmlization::From(
{II}ifs
{I});

{I}if (deserialized.has_value()) {{
{II}INFO(
{III}aas::common::Concat(
{IIII}"Expected the de-serialization to fail on ",
{IIII}path.string(),
{IIII}", but the de-serialization succeeded"
{III})
{II})
{II}REQUIRE(!deserialized.has_value());
{I}}}

{I}test::common::AssertContentEqualsExpectedOrRecord(
{II}aas::common::Concat(
{III}aas::common::WstringToUtf8(
{IIII}deserialized.error().path.ToWstring()
{III}),
{III}": ",
{III}aas::common::WstringToUtf8(
{IIII}deserialized.error().cause
{III})
{II}),
{II}error_path
{I});
}}"""
        ),
        Stripped(
            f"""\
const std::filesystem::path& DetermineXmlDir() {{
{I}static aas::common::optional<std::filesystem::path> result;
{I}if (!result.has_value()) {{
{II}result = test::common::DetermineTestDataDir() / "Xml";
{I}}}

{I}return *result;
}}"""
        ),
        Stripped(
            f"""\
const std::filesystem::path& DetermineErrorDir() {{
{I}static aas::common::optional<std::filesystem::path> result;
{I}if (!result.has_value()) {{
{II}result = test::common::DetermineTestDataDir() / "XmlizationError";
{I}}}

{I}return *result;
}}"""
        ),
    ]  # type: List[Stripped]

    for concrete_cls in symbol_table.concrete_classes:
        xml_class_name = naming.xml_class_name(concrete_cls.name)

        cls_name = cpp_naming.class_name(concrete_cls.name)

        blocks.append(
            Stripped(
                f"""\
TEST_CASE("Test the round-trip of an expected {cls_name}") {{
{I}const std::deque<std::filesystem::path> paths(
{II}test::common::FindFilesBySuffixRecursively(
{III}DetermineXmlDir()
{IIII}/ "Expected"
{IIII}/ {cpp_common.string_literal(xml_class_name)},
{III}".xml"
{II})
{I});

{I}for (const std::filesystem::path &path : paths) {{
{II}AssertRoundTrip(path);
{I}}}
}}"""
            )
        )

        blocks.append(
            Stripped(
                f"""\
TEST_CASE("Test the de-serialization failure on an unexpected {cls_name}") {{
{I}for (
{II}const std::filesystem::path& causeDir
{II}: test::common::ListSubdirectories(
{III}DetermineXmlDir()
{IIII}/ "Unexpected"
{IIII}/ "Unserializable"
{II})
{I}) {{
{II}for (
{III}const std::filesystem::path& path
{III}: test::common::FindFilesBySuffixRecursively(
{IIII}causeDir / {cpp_common.string_literal(xml_class_name)},
{IIII}".xml"
{III})
{II}) {{
{III}const std::filesystem::path parent(
{IIII}(
{IIIII}DetermineErrorDir()
{IIIII}/ std::filesystem::relative(path, DetermineXmlDir())
{IIII}).parent_path()
{III});

{III}const std::filesystem::path error_path(
{IIII}parent
{IIII}/ (path.filename().string() + ".error")
{III});

{III}AssertDeserializationFailure(
{IIII}path,
{IIII}error_path
{III});
{II}}}
{I}}}
}}"""
            )
        )

    blocks.append(cpp_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate_implementation.__doc__ is not None
cpp_common.assert_module_docstring_and_generate_implementation_consistent(
    module_doc=__doc__, generate_implementation_doc=generate_implementation.__doc__
)
