"""Generate code to test the jsonization of concrete classes."""

import io
from typing import List

from icontract import ensure

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import (
    Stripped,
    Identifier,
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
    """Generate implementation to test the jsonization of concrete classes."""
    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            f"""\
#include "./common.hpp"
#include "./common_jsonization.hpp"

#include <{include_prefix_path}/jsonization.hpp>

#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>

namespace aas = {library_namespace};"""
        ),
        Stripped(
            f"""\
template<class ClassT>
void AssertRoundTrip(
{I}const std::filesystem::path& path,
{I}std::function<
{II}aas::common::expected<
{III}std::shared_ptr<ClassT>,
{III}aas::jsonization::DeserializationError
{II}>(const nlohmann::json&, bool)
{I}> deserialization_function
) {{
{I}const nlohmann::json json = test::common::jsonization::MustReadJson(path);

{I}aas::common::expected<
{II}std::shared_ptr<ClassT>,
{II}aas::jsonization::DeserializationError
{I}> deserialized = deserialization_function(json, false);

{I}if (!deserialized.has_value()) {{
{II}INFO(
{III}aas::common::Concat(
{IIII}"Failed to de-serialize from ",
{IIII}path.string(),
{IIII}": ",
{IIII}aas::common::WstringToUtf8(
{IIIII}deserialized.error().path.ToWstring()
{IIII}),
{IIII}": ",
{IIII}aas::common::WstringToUtf8(
{IIIII}deserialized.error().cause
{IIII})
{III})
{II})
{II}REQUIRE(deserialized.has_value());
{I}}}

{I}nlohmann::json another_json = aas::jsonization::Serialize(
{II}*(deserialized.value())
{I});

{I}std::optional<std::string> diff_message = test::common::jsonization::CompareJsons(
{II}json,
{II}another_json
{I});
{I}if (diff_message.has_value()) {{
{II}INFO(
{III}aas::common::Concat(
{IIII}"The JSON round-trip from ",
{IIII}path.string(),
{IIII}" failed. There is a diff between the original JSON "
{IIII}"and the serialized one: ",
{IIII}*diff_message
{III})
{II})
{II}REQUIRE(!diff_message.has_value());
{I}}}
}}"""
        ),
        Stripped(
            f"""\
template<typename ClassT>
void AssertDeserializationFailure(
{I}const std::filesystem::path& path,
{I}std::function<
{II}aas::common::expected<
{III}std::shared_ptr<ClassT>,
{III}aas::jsonization::DeserializationError
{II}>(const nlohmann::json&, bool)
{I}> deserialization_function,
{I}const std::filesystem::path& error_path
) {{
{I}const nlohmann::json json = test::common::jsonization::MustReadJson(path);

{I}aas::common::expected<
{II}std::shared_ptr<ClassT>,
{II}aas::jsonization::DeserializationError
{I}> deserialized = deserialization_function(json, false);

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
const std::filesystem::path& DetermineJsonDir() {{
{I}static aas::common::optional<std::filesystem::path> result;
{I}if (!result.has_value()) {{
{II}result = test::common::DetermineTestDataDir() / "Json";
{I}}}

{I}return *result;
}}"""
        ),
        Stripped(
            f"""\
const std::filesystem::path& DetermineErrorDir() {{
{I}static aas::common::optional<std::filesystem::path> result;
{I}if (!result.has_value()) {{
{II}result = test::common::DetermineTestDataDir() / "JsonizationError";
{I}}}

{I}return *result;
}}"""
        ),
    ]  # type: List[Stripped]

    for concrete_cls in symbol_table.concrete_classes:
        interface_name = cpp_naming.interface_name(concrete_cls.name)

        model_type = naming.json_model_type(concrete_cls.name)

        deserialization_function = cpp_naming.function_name(
            Identifier(f"{concrete_cls.name}_from")
        )

        cls_name = cpp_naming.class_name(concrete_cls.name)

        blocks.append(
            Stripped(
                f"""\
TEST_CASE("Test the round-trip of an expected {cls_name}") {{
{I}const std::deque<std::filesystem::path> paths(
{II}test::common::FindFilesBySuffixRecursively(
{III}DetermineJsonDir()
{IIII}/ "Expected"
{IIII}/ {cpp_common.string_literal(model_type)},
{III}".json"
{II})
{I});

{I}for (const std::filesystem::path& path : paths) {{
{II}AssertRoundTrip<
{III}aas::types::{interface_name}
{II}>(path, aas::jsonization::{deserialization_function});
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
{III}DetermineJsonDir()
{IIII}/ "Unexpected"
{IIII}/ "Unserializable"
{II})
{I}) {{
{II}for (
{III}const std::filesystem::path& path
{III}: test::common::FindFilesBySuffixRecursively(
{IIII}causeDir / {cpp_common.string_literal(model_type)},
{IIII}".json"
{III})
{II}) {{
{III}const std::filesystem::path parent(
{IIII}(
{IIIII}DetermineErrorDir()
{IIIII}/ std::filesystem::relative(path, DetermineJsonDir())
{IIII}).parent_path()
{III});

{III}const std::filesystem::path error_path(
{IIII}parent
{IIII}/ (path.filename().string() + ".error")
{III});

{III}AssertDeserializationFailure<
{IIII}aas::types::{interface_name}
{III}>(
{IIII}path,
{IIII}aas::jsonization::{deserialization_function},
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
