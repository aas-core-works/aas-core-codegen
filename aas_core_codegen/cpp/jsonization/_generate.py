"""Generate C++ code for de/serialization of instances from JSON."""

import io
import itertools
from typing import List, Tuple, Optional, Iterable

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations, naming
from aas_core_codegen.common import (
    Stripped,
    indent_but_first_line,
    Identifier,
    Error,
    assert_never,
)
from aas_core_codegen.cpp import common as cpp_common, naming as cpp_naming
from aas_core_codegen.cpp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
)


def _generate_deserialization_definitions(
    symbol_table: intermediate.SymbolTable,
) -> List[Stripped]:
    """Generate the definitions of deserialization functions."""
    blocks = []  # type: List[Stripped]

    for cls in symbol_table.classes:
        interface_name = cpp_naming.interface_name(cls.name)
        deserialization_name = cpp_naming.function_name(Identifier(f"{cls.name}_from"))

        blocks.append(
            Stripped(
                f"""\
/**
 * \\brief Deserialize \\p json value to an instance
 * of types::{interface_name}.
 *
 * \\param json value to be de-serialized
 * \\param additional_properties if not set, check that \\p json contains
 * no additional properties
 * \\return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
{I}std::shared_ptr<types::{interface_name}>,
{I}DeserializationError
> {deserialization_name}(
{I}const nlohmann::json& json,
{I}bool additional_properties = false
);"""
            )
        )

    return blocks


# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate_header(
    symbol_table: intermediate.SymbolTable, library_namespace: Stripped
) -> str:
    """Generate the C++ header code for JSON de/serialization."""
    namespace = Stripped(f"{library_namespace}::{cpp_common.JSONIZATION_NAMESPACE}")

    include_guard_var = cpp_common.include_guard_var(namespace)

    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        Stripped(
            f"""\
#ifndef {include_guard_var}
#define {include_guard_var}"""
        ),
        cpp_common.WARNING,
        Stripped(
            f"""\
#include "{include_prefix_path}/common.hpp"
#include "{include_prefix_path}/iteration.hpp"
#include "{include_prefix_path}/types.hpp"

#pragma warning(push, 0)
#include <nlohmann/json.hpp>

#include <memory>
#include <string>
#include <utility>
#pragma warning(pop)"""
        ),
        cpp_common.generate_namespace_opening(library_namespace),
        Stripped(
            f"""\
/**
 * \\defgroup jsonization De/serialize instances from and to JSON.
 * @{{
 */
namespace {cpp_common.JSONIZATION_NAMESPACE} {{"""
        ),
        Stripped(
            f"""\
/**
 * Represent a segment of a JSON path to some value.
 */
class ISegment {{
 public:
{I}/**
{I} * \\brief Convert the segment to a string in a JSON path.
{I} */
{I}virtual std::wstring ToWstring() const = 0;

{I}virtual std::unique_ptr<ISegment> Clone() const = 0;

{I}virtual ~ISegment() = default;
}};  // class ISegment"""
        ),
        Stripped(
            f"""\
/**
 * Represent a property access on a JSON path.
 */
struct PropertySegment : public ISegment {{
{I}/**
{I} * Name of the property in a JSON object
{I} */
{I}std::wstring name;

{I}PropertySegment(
{II}std::wstring a_name
{I});

{I}std::wstring ToWstring() const override;

{I}std::unique_ptr<ISegment> Clone() const override;

{I}~PropertySegment() override = default;
}};  // struct PropertySegment"""
        ),
        Stripped(
            f"""\
/**
 * Represent an index access on a JSON path.
 */
struct IndexSegment : public ISegment {{
{I}/**
{I} * Index of the value in an array.
{I} */
{I}size_t index;

{I}explicit IndexSegment(
{II}size_t an_index
{I});

{I}std::wstring ToWstring() const override;

{I}std::unique_ptr<ISegment> Clone() const override;

{I}~IndexSegment() override = default;
}};  // struct IndexSegment"""
        ),
        Stripped(
            f"""\
/**
 * Represent a JSON path to some value.
 */
struct Path {{
{I}std::deque<std::unique_ptr<ISegment> > segments;

{I}Path();
{I}Path(const Path& other);
{I}Path(Path&& other);
{I}Path& operator=(const Path& other);
{I}Path& operator=(Path&& other);

{I}std::wstring ToWstring() const;
}};  // struct Path"""
        ),
        Stripped("// region De-serialization"),
        Stripped(
            f"""\
/**
 * Represent a de-serialization error.
 */
struct DeserializationError {{
{I}/**
{I} * Human-readable description of the error
{I} */
{I}std::wstring cause;

{I}/**
{I} * Path to the erroneous value
{I} */
{I}Path path;

{I}explicit DeserializationError(std::wstring a_cause);
{I}DeserializationError(std::wstring a_cause, Path a_path);
}};  // struct DeserializationError"""
        ),
        *_generate_deserialization_definitions(symbol_table=symbol_table),
        Stripped("// endregion Deserialization"),
        Stripped("// region Serialization"),
        Stripped(
            f"""\
/**
 * Represent an error in the serialization of an instance to JSON.
 */
class SerializationException : public std::exception {{
 public:
{I}SerializationException(
{II}std::wstring cause,
{II}iteration::Path path
{I});

{I}const char* what() const noexcept override;

{I}const std::wstring& cause() const noexcept;
{I}const iteration::Path& path() const noexcept;

{I}~SerializationException() noexcept override = default;

 private:
{I}const std::wstring cause_;
{I}const iteration::Path path_;
{I}const std::string msg_;
}};  // class SerializationException"""
        ),
        Stripped(
            f"""\
/**
 * \\brief Serialize \\p that instance to a JSON value.
 *
 * \\param that instance to be serialized
 * \\return The corresponding JSON value
 * \\throw \\ref SerializationException if a value within \\p that instance
 * could not be serialized
 */
nlohmann::json Serialize(
{I}const types::IClass& that
);"""
        ),
        Stripped("// endregion Serialization"),
        Stripped(
            f"""\
}}  // namespace {cpp_common.JSONIZATION_NAMESPACE}
/**@}}*/"""
        ),
        cpp_common.generate_namespace_closing(library_namespace),
        cpp_common.WARNING,
        Stripped(f"#endif  // {include_guard_var}"),
    ]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


def _generate_property_segment_implementation() -> List[Stripped]:
    """Generate the implementation of the struct ``PropertySegment``."""
    return [
        Stripped("// region PropertySegment"),
        Stripped(
            f"""\
PropertySegment::PropertySegment(
{I}std::wstring a_name
) :
{I}name(std::move(a_name)) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
std::wstring PropertySegment::ToWstring() const {{
{I}return common::Concat(
{II}L".",
{II}name
{I});
}}"""
        ),
        Stripped(
            f"""\
std::unique_ptr<ISegment> PropertySegment::Clone() const {{
{I}return common::make_unique<PropertySegment>(*this);
}}"""
        ),
        Stripped("// endregion PropertySegment"),
    ]


def _generate_index_segment_implementation() -> List[Stripped]:
    """Generate the implementation of the struct ``IndexSegment``."""
    return [
        Stripped("// region IndexSegment"),
        Stripped(
            f"""\
IndexSegment::IndexSegment(
{I}size_t an_index
) :
{I}index(an_index) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
std::wstring IndexSegment::ToWstring() const {{
{I}return common::Concat(
{II}L"[",
{II}std::to_wstring(index),
{II}L"]"
{I});
}}"""
        ),
        Stripped(
            f"""\
std::unique_ptr<ISegment> IndexSegment::Clone() const {{
{I}return common::make_unique<IndexSegment>(*this);
}}"""
        ),
        Stripped("// endregion IndexSegment"),
    ]


def _generate_path_implementation() -> List[Stripped]:
    """Generate the implementation of the struct ``Path``."""
    return [
        Stripped("// region struct Path"),
        Stripped(
            f"""\
Path::Path() {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
Path::Path(const Path& other) {{
{I}for (const std::unique_ptr<ISegment>& segment : other.segments) {{
{II}segments.emplace_back(segment->Clone());
{I}}}
}}"""
        ),
        Stripped(
            f"""\
Path::Path(Path&& other) {{
{I}segments = std::move(other.segments);
}}"""
        ),
        Stripped(
            f"""\
Path& Path::operator=(const Path& other) {{
{I}segments.clear();
{I}for (const std::unique_ptr<ISegment>& segment : other.segments) {{
{II}segments.emplace_back(segment->Clone());
{I}}}
{I}return *this;
}}"""
        ),
        Stripped(
            f"""\
Path& Path::operator=(Path&& other) {{
{I}if (this != &other) {{
{II}segments = std::move(other.segments);
{I}}}
{I}return *this;
}}"""
        ),
        Stripped(
            f"""\
std::wstring Path::ToWstring() const {{
{I}if (segments.empty()) {{
{II}return L"";
{I}}}

{I}std::deque<std::wstring> parts;
{I}for (const std::unique_ptr<ISegment>& segment : segments ) {{
{II}parts.emplace_back(segment->ToWstring());
{I}}}

{I}size_t out_len = 0;
{I}for (const std::wstring& part : parts) {{
{II}out_len += part.size();
{I}}}

{I}std::wstring out;
{I}out.reserve(out_len);
{I}for (const std::wstring& part : parts) {{
{II}out.append(part);
{I}}}

{I}return out;
}}"""
        ),
        Stripped("// endregion struct Path"),
    ]


def _generate_deserialization_error_implementation() -> List[Stripped]:
    """Generate the impl. of the deserialization error class."""
    return [
        Stripped("// region class DeserializationError"),
        Stripped(
            f"""\
DeserializationError::DeserializationError(
{I}std::wstring a_cause
) :
{I}cause(a_cause) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
DeserializationError::DeserializationError(
{I}std::wstring a_cause,
{I}Path a_path
) :
{I}cause(a_cause),
{I}path(a_path) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped("// endregion class DeserializationError"),
    ]


def _generate_deserialize_bool() -> Stripped:
    """Generate the function to de-serialize a boolean from a JSON value."""
    return Stripped(
        f"""\
std::pair<
{I}common::optional<bool>,
{I}common::optional<DeserializationError>
> DeserializeBool(
{I}const nlohmann::json& json
) {{
{I}if (!json.is_boolean()) {{
{II}std::wstring message = common::Concat(
{III}L"Expected a boolean, but got a value of type: ",
{III}common::Utf8ToWstring(json.type_name())
{II});

{II}return std::make_pair<
{III}common::optional<bool>,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}return std::make_pair<
{II}common::optional<bool>,
{II}common::optional<DeserializationError>
{I}>(
{II}json.get<bool>(),
{II}common::nullopt
{I});
}}"""
    )


def _generate_deserialize_int() -> Stripped:
    """Generate the function to de-serialize an int from a JSON value."""
    return Stripped(
        f"""\
std::pair<
{I}common::optional<int64_t>,
{I}common::optional<DeserializationError>
> DeserializeInt64(
{I}const nlohmann::json& json
) {{
{I}if (!json.is_number()) {{
{II}std::wstring message = common::Concat(
{III}L"Expected an integer number, but got a value of type: ",
{III}common::Utf8ToWstring(json.type_name())
{II});

{II}return std::make_pair<
{III}common::optional<int64_t>,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}static_assert(
{II}std::is_same<nlohmann::json::number_integer_t, int64_t>::value,
{II}"Expected nlohmann::json::number_integer_t to equal int64_t, "
{II}"but it does not."
{I});

{I}if (json.is_number_integer()) {{
{II}return std::make_pair<
{III}common::optional<int64_t>,
{III}common::optional<DeserializationError>
{II}>(
{III}json.get<int64_t>(),
{III}common::nullopt
{II});
{I}}}

{I}if (json.is_number_unsigned()) {{
{II}std::wstring message = common::Concat(
{III}L"Expected a 64-bit integer number, "
{III}L"but got an unsigned integer number which does not fit in that range: ",
{III}std::to_wstring(json.get<nlohmann::json::number_unsigned_t>())
{II});

{II}return std::make_pair<
{III}common::optional<int64_t>,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}// NOTE (mristin):
{I}// We have to check that the number is an integer even though it can
{I}// not be stored in int64_t in order to give an informative message.

{I}const nlohmann::json::number_float_t number(
{II}json.get<nlohmann::json::number_float_t>()
{I});

{I}nlohmann::json::number_float_t integer_part;
{I}const bool is_integer(
{II}std::modf(number, &integer_part) == 0
{I});
{I}if (is_integer) {{
{II}std::wstring message = common::Concat(
{III}L"Expected a 64-bit integer number, "
{III}L"but got an integer number which does not fit in that range: ",
{III}std::to_wstring(number)
{II});

{II}return std::make_pair<
{III}common::optional<int64_t>,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}} else {{
{II}std::wstring message = common::Concat(
{III}L"Expected a 64-bit integer number, "
{III}L"but got a non-integer number: ",
{III}std::to_wstring(number)
{II});

{II}return std::make_pair<
{III}common::optional<int64_t>,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}
}}"""
    )


def _generate_deserialize_float() -> Stripped:
    """Generate the function to de-serialize a float from a JSON value."""
    return Stripped(
        f"""\
std::pair<
{I}common::optional<double>,
{I}common::optional<DeserializationError>
> DeserializeDouble(
{I}const nlohmann::json& json
) {{
{I}if (!json.is_number()) {{
{II}std::wstring message = common::Concat(
{III}L"Expected a number, but got a value of type: ",
{III}common::Utf8ToWstring(json.type_name())
{II});

{II}return std::make_pair<
{III}common::optional<double>,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}static_assert(
{II}std::is_same<nlohmann::json::number_float_t, double>::value,
{II}"Expected nlohmann::json::number_float_t to equal double, "
{II}"but it does not."
{I});

{I}return std::make_pair<
{II}common::optional<double>,
{II}common::optional<DeserializationError>
{I}>(
{II}json.get<double>(),
{II}common::nullopt
{I});
}}"""
    )


def _generate_deserialize_str() -> Stripped:
    """Generate the function to de-serialize a string from a JSON value."""
    return Stripped(
        f"""\
std::pair<
{I}common::optional<std::wstring>,
{I}common::optional<DeserializationError>
> DeserializeWstring(
{I}const nlohmann::json& json
) {{
{I}if (!json.is_string()) {{
{II}std::wstring message = common::Concat(
{III}L"Expected a string, but got a value of type: ",
{III}common::Utf8ToWstring(json.type_name())
{II});

{II}return std::make_pair<
{III}common::optional<std::wstring>,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}return std::make_pair<
{II}common::optional<std::wstring>,
{II}common::optional<DeserializationError>
{I}>(
{II}common::Utf8ToWstring(*(json.get_ptr<const std::string*>())),
{II}common::nullopt
{I});
}}"""
    )


def _generate_deserialize_bytearray() -> Stripped:
    """Generate the function to de-serialize a bytearray from a JSON value."""
    return Stripped(
        f"""\
std::pair<
{I}common::optional<std::vector<std::uint8_t> >,
{I}common::optional<DeserializationError>
> DeserializeByteArray(
{I}const nlohmann::json& json
) {{
{I}if (!json.is_string()) {{
{II}std::wstring message = common::Concat(
{III}L"Expected a base64-encoded byte array as a string, "
{III}L"but got a value of type: ",
{III}common::Utf8ToWstring(json.type_name())
{II});;

{II}return std::make_pair<
{III}common::optional<std::vector<std::uint8_t> >,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}common::expected<
{II}std::vector<std::uint8_t>,
{II}std::string
{I}> bytes = stringification::Base64Decode(
{II}*(json.get_ptr<const std::string*>())
{I});

{I}if (!bytes.has_value()) {{
{II}std::wstring message = common::Concat(
{III}L"Failed to base64-decode the bytes from a string: ",
{III}common::Utf8ToWstring(bytes.error())
{II});

{II}return std::make_pair<
{III}common::optional<std::vector<std::uint8_t> >,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}return std::make_pair<
{II}common::optional<std::vector<std::uint8_t> >,
{II}common::optional<DeserializationError>
{I}>(
{II}std::move(*bytes),
{II}common::nullopt
{I});
}}"""
    )


_PRIMITIVE_TYPE_TO_DESERIALIZE = {
    intermediate.PrimitiveType.BOOL: "DeserializeBool",
    intermediate.PrimitiveType.INT: "DeserializeInt64",
    intermediate.PrimitiveType.FLOAT: "DeserializeDouble",
    intermediate.PrimitiveType.STR: "DeserializeWstring",
    intermediate.PrimitiveType.BYTEARRAY: "DeserializeByteArray",
}
assert all(
    primitive_type in _PRIMITIVE_TYPE_TO_DESERIALIZE
    for primitive_type in intermediate.PrimitiveType
)

_PRIMITIVE_TYPE_TO_NATIVE_TYPE = {
    intermediate.PrimitiveType.BOOL: "bool",
    intermediate.PrimitiveType.INT: "int64_t",
    intermediate.PrimitiveType.FLOAT: "double",
    intermediate.PrimitiveType.STR: "std::wstring",
    intermediate.PrimitiveType.BYTEARRAY: "std::vector<std::uint8_t>",
}
assert all(
    primitive_type in _PRIMITIVE_TYPE_TO_NATIVE_TYPE
    for primitive_type in intermediate.PrimitiveType
)


def _generate_get_model_type() -> Stripped:
    """Generate the getter of the model type from JSON object for dispatches."""
    return Stripped(
        f"""\
/**
 * Get the property `modelType` from the JSON value expected as a JSON object.
 */
std::pair<
{I}const std::string*,
{I}common::optional<DeserializationError>
> GetModelTypeFrom(
{I}const nlohmann::json& json
) {{
{I}if (!json.is_object()) {{
{II}std::wstring message = common::Concat(
{III}L"Expected an object, but got: ",
{III}common::Utf8ToWstring(json.type_name())
{II});

{II}return std::make_pair<
{III}const std::string*,
{III}common::optional<DeserializationError>
{II}>(
{III}nullptr,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}if (!json.contains("modelType")) {{
{II}return std::make_pair<
{III}const std::string*,
{III}common::optional<DeserializationError>
{II}>(
{III}nullptr,
{III}common::make_optional<DeserializationError>(
{IIII}L"The required property modelType is missing"
{III})
{II});
{I}}}

{I}const nlohmann::json& model_type_prop = json["modelType"];
{I}if (!model_type_prop.is_string()) {{
{II}std::wstring message = common::Concat(
{III}L"Expected modelType to be a string, but got: ",
{III}common::Utf8ToWstring(model_type_prop.type_name())
{II});

{II}common::optional<DeserializationError> error(
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{II}error->path.segments.emplace_front(
{III}common::make_unique<PropertySegment>(
{IIII}L"modelType"
{III})
{II});

{II}// NOTE (mristin):
{II}// We have to explicitly use the constructor instead of std::make_pair
{II}// as `const std::string*` can not be automatically converted to a rvalue.
{II}return std::pair<
{III}const std::string*,
{III}common::optional<DeserializationError>
{II}>(
{III}nullptr,
{III}error
{II});
{I}}}

{I}static_assert(
{II}std::is_same<nlohmann::json::string_t, std::string>::value,
{II}"Expected nlohmann::json::string_t to equal std::string, but it does not."
{I});

{I}const std::string* model_type(
{II}model_type_prop.get_ptr<const std::string*>()
{I});

{I}// NOTE (mristin):
{I}// We have to explicitly use the constructor instead of std::make_pair
{I}// as `const std::string*` can not be automatically converted to a rvalue.
{I}return std::pair<
{II}const std::string*,
{II}common::optional<DeserializationError>
{I}>(
{II}model_type,
{II}common::nullopt
{I});
}}"""
    )


def _generate_concretely_deserialize_definition(
    cls: intermediate.ClassUnion,
) -> Stripped:
    """Generate the definition of the concrete ``Deserialize*`` functions."""
    interface_name = cpp_naming.interface_name(cls.name)

    if len(cls.concrete_descendants) == 0:
        function_name = cpp_naming.function_name(Identifier(f"deserialize_{cls.name}"))
    else:
        function_name = cpp_naming.function_name(
            Identifier(f"concretely_deserialize_{cls.name}")
        )

    if len(cls.ancestors) > 0:
        # NOTE (mristin, 2023-11-10):
        # We have to introduce the template so that we do not have to
        # unnecessarily upcast the instance to ancestor classes.
        prefix = Stripped(
            f"""\
template <
{I}typename T,
{I}typename std::enable_if<
{II}std::is_base_of<T, types::{interface_name}>::value
{I}>::type* = nullptr
>
std::pair<
{I}common::optional<std::shared_ptr<T> >,
{I}common::optional<DeserializationError>
>"""
        )
    else:
        prefix = Stripped(
            f"""\
std::pair<
{I}common::optional<
{II}std::shared_ptr<types::{interface_name}>
{I}>,
{I}common::optional<DeserializationError>
>"""
        )

    return Stripped(
        f"""\
/**
 * \\brief Deserialize concretely an instance
 * of types::{interface_name}.
 *
 * \\param json value to be de-serialized
 * \\param additional_properties if not set, check that \\p json contains
 * no additional properties
 * \\return the deserialized instance, or an error, if any
 */
{prefix} {function_name}(
{I}const nlohmann::json& json,
{I}bool additional_properties
);"""
    )


@require(
    lambda cls: len(cls.concrete_descendants) > 0,
    "No dispatch possible without concrete descendants",
)
def _generate_dispatch_deserialize_definition(cls: intermediate.ClassUnion) -> Stripped:
    """Generate the def. of the dispatching deserialization function for ``cls``."""
    interface_name = cpp_naming.interface_name(cls.name)

    function_name = cpp_naming.function_name(Identifier(f"deserialize_{cls.name}"))

    return Stripped(
        f"""\
/**
 * \\brief Dispatch the deserialization for an instance
 * of types::{interface_name}.
 *
 * \\param json value to be de-serialized
 * \\param additional_properties if not set, check that \\p json contains
 * no additional properties
 * \\return the deserialized instance, or an error, if any
 */
std::pair<
{I}common::optional<
{II}std::shared_ptr<types::{interface_name}>
{I}>,
{I}common::optional<DeserializationError>
> {function_name}(
{I}const nlohmann::json& json,
{I}bool additional_properties
);"""
    )


def _generate_deserialize_primitive_property(
    prop: intermediate.Property, ok_type: Stripped
) -> Stripped:
    """
    Generate the snippet to de-serialize the primitive property.

    We assume that the check whether the property is set is performed elsewhere.

    The ``ok_type`` denotes the type of the deserialized instance, *not* the property.
    We have to distinguish between cases where we directly create an upcast pointer to
    an ancestor class, and cases where there are no ancestor classes.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    primitive_type = intermediate.try_primitive_type(type_anno)

    assert (
        primitive_type is not None
    ), f"Primitive property expected, got for {prop.name!r}: {prop.type_annotation}"

    deserialize_primitive = _PRIMITIVE_TYPE_TO_DESERIALIZE[primitive_type]

    json_prop_name = naming.json_property(prop.name)

    var_name = cpp_naming.variable_name(Identifier(f"the_{prop.name}"))

    return Stripped(
        f"""\
std::tie(
{I}{var_name},
{I}error
) = {deserialize_primitive}(
{I}json[{cpp_common.string_literal(json_prop_name)}]
);

if (error.has_value()) {{
{I}error->path.segments.emplace_front(
{II}common::make_unique<PropertySegment>(
{III}{cpp_common.wstring_literal(json_prop_name)}
{II})
{I});

{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}"""
    )


def _generate_deserialize_enumeration_property(
    prop: intermediate.Property, ok_type: Stripped
) -> Stripped:
    """
    Generate the snippet to de-serialize the enumeration property.

    We assume that the check whether the property is set is performed elsewhere.

    The ``ok_type`` denotes the type of the deserialized instance, *not* the property.
    We have to distinguish between cases where we directly create an upcast pointer to
    an ancestor class, and cases where there are no ancestor classes.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
        type_anno.our_type, intermediate.Enumeration
    )

    enum = type_anno.our_type
    enum_name = cpp_naming.enum_name(enum.name)

    from_wstring = cpp_naming.function_name(Identifier(f"{enum.name}_from_wstring"))

    json_prop_name = naming.json_property(prop.name)

    var_name = cpp_naming.variable_name(Identifier(f"the_{prop.name}"))
    var_text_name = cpp_naming.variable_name(Identifier(f"text_{prop.name}"))

    return Stripped(
        f"""\
common::optional<std::wstring> {var_text_name};

std::tie(
{I}{var_text_name},
{I}error
) = DeserializeWstring(
{I}json[{cpp_common.string_literal(json_prop_name)}]
);

if (error.has_value()) {{
{I}error->path.segments.emplace_front(
{II}common::make_unique<PropertySegment>(
{III}{cpp_common.wstring_literal(json_prop_name)}
{II})
{I});

{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}

{var_name} = std::move(
{I}wstringification::{from_wstring}(
{II}*{var_text_name}
{I})
);
if (!{var_name}.has_value()) {{
{I}std::wstring message = common::Concat(
{II}L"Invalid literal for {enum_name}: ",
{II}*{var_text_name}
{I});

{I}error = common::make_optional<DeserializationError>(
{II}message
{I});
{I}error->path.segments.emplace_front(
{II}common::make_unique<PropertySegment>(
{III}{cpp_common.wstring_literal(json_prop_name)}
{II})
{I});

{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}"""
    )


def _determine_deserialize_function_to_call(cls: intermediate.ClassUnion) -> Stripped:
    """
    Determine the function to be called to de-serialize an instance of ``cls``.

    The result includes also template parameters, if any are necessary.
    """
    deserialize_name = cpp_naming.function_name(Identifier(f"Deserialize_{cls.name}"))

    interface_name = cpp_naming.interface_name(cls.name)

    if len(cls.concrete_descendants) == 0:
        if len(cls.ancestors) == 0:
            deserialize_function = Stripped(deserialize_name)
        else:
            deserialize_function = Stripped(
                f"""\
{deserialize_name}<
{I}types::{interface_name}
>"""
            )
    else:
        deserialize_function = Stripped(deserialize_name)

    return deserialize_function


def _generate_deserialize_instance_property(
    prop: intermediate.Property, ok_type: Stripped
) -> Stripped:
    """
    Generate the snippet to de-serialize the instance property.

    We assume that the check whether the property is set is performed elsewhere.

    The ``ok_type`` denotes the type of the deserialized instance, *not* the property.
    We have to distinguish between cases where we directly create an upcast pointer to
    an ancestor class, and cases where there are no ancestor classes.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
        type_anno.our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
    )

    cls = type_anno.our_type

    deserialize_function = _determine_deserialize_function_to_call(cls=cls)

    var_name = cpp_naming.variable_name(Identifier(f"the_{prop.name}"))
    json_prop_name = naming.json_property(prop.name)

    return Stripped(
        f"""\
std::tie(
{I}{var_name},
{I}error
) = {deserialize_function}(
{I}json[{cpp_common.string_literal(json_prop_name)}],
{I}additional_properties
);

if (error.has_value()) {{
{I}error->path.segments.emplace_front(
{II}common::make_unique<PropertySegment>(
{III}{cpp_common.wstring_literal(json_prop_name)}
{II})
{I});

{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}"""
    )


def _generate_deserialize_list_property(
    prop: intermediate.Property, ok_type: Stripped
) -> Stripped:
    """
    Generate the snippet to de-serialize the list property.

    We assume that the check whether the property is set is performed elsewhere.

    The ``ok_type`` denotes the type of the deserialized instance, *not* the property.
    We have to distinguish between cases where we directly create an upcast pointer to
    an ancestor class, and cases where there are no ancestor classes.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.ListTypeAnnotation)
    assert (
        isinstance(type_anno.items, intermediate.PrimitiveTypeAnnotation)
        or isinstance(type_anno.items, intermediate.OurTypeAnnotation)
        and isinstance(
            type_anno.items.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        )
    ), (
        f"NOTE (mristin, 2023-11-10): We expect only lists of classes "
        f"at the moment, but you specified {type_anno}. "
        f"Please contact the developers if you need this feature."
    )

    if isinstance(type_anno.items, intermediate.PrimitiveTypeAnnotation):
        primitive_type = intermediate.try_primitive_type(type_anno.items)
        interface_name = _PRIMITIVE_TYPE_TO_NATIVE_TYPE[primitive_type]
        deserialize_function = _PRIMITIVE_TYPE_TO_DESERIALIZE[primitive_type]
    else:
        cls = type_anno.items.our_type
        interface_name = f"types::{cpp_naming.interface_name(cls.name)}"
        deserialize_function = _determine_deserialize_function_to_call(cls=cls)

    var_name = cpp_naming.variable_name(Identifier(f"the_{prop.name}"))
    json_prop_name = naming.json_property(prop.name)

    var_index_name = cpp_naming.variable_name(Identifier(f"index_{prop.name}"))
    var_json = cpp_naming.variable_name(Identifier(f"json_{prop.name}"))

    return Stripped(
        f"""\
const nlohmann::json& {var_json}(
{I}json[{cpp_common.string_literal(json_prop_name)}]
);
if (!{var_json}.is_array()) {{
{I}error = common::make_optional<DeserializationError>(
{II}common::Concat(
{III}L"Expected an array, but got: ",
{III}common::Utf8ToWstring(
{IIII}{var_json}.type_name()
{III})
{II})
{I});

{I}error->path.segments.emplace_front(
{II}common::make_unique<PropertySegment>(
{III}{cpp_common.wstring_literal(json_prop_name)}
{II})
{I});

{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}

{var_name} = common::make_optional<
{I}std::vector<
{II}std::shared_ptr<{interface_name}>
{I}>
>();

{var_name}->reserve({var_json}.size());

size_t {var_index_name} = 0;

for (
{I}const nlohmann::json& item
{I}: {var_json}
) {{
{I}common::optional<
{II}std::shared_ptr<{interface_name}>
{I}> deserialized;

{I}std::tie(
{II}deserialized,
{II}error
{I}) = {indent_but_first_line(deserialize_function, I)}(
{II}item,
{II}additional_properties
{I});

{I}if (error.has_value()) {{
{II}error->path.segments.emplace_front(
{III}common::make_unique<IndexSegment>(
{IIII}{var_index_name}
{III})
{II});

{II}error->path.segments.emplace_front(
{III}common::make_unique<PropertySegment>(
{IIII}{cpp_common.wstring_literal(json_prop_name)}
{III})
{II});

{II}return std::make_pair<
{III}common::optional<std::shared_ptr<{ok_type}> >,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}std::move(error)
{II});
{I}}}

{I}{var_name}->emplace_back(
{II}std::move(*deserialized)
{I});

{I}++{var_index_name};
}}"""
    )


def _generate_deserialize_property(
    prop: intermediate.Property, ok_type: Stripped
) -> Stripped:
    """
    Generate the snippet to de-serialize the given property.

    The ``ok_type`` denotes the type of the deserialized instance, *not* the property.
    We have to distinguish between cases where we directly create an upcast pointer to
    an ancestor class, and cases where there are no ancestor classes.
    """
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    code: Stripped

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        code = _generate_deserialize_primitive_property(prop=prop, ok_type=ok_type)

    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        if isinstance(type_anno.our_type, intermediate.Enumeration):
            code = _generate_deserialize_enumeration_property(
                prop=prop, ok_type=ok_type
            )

        elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
            code = _generate_deserialize_primitive_property(prop=prop, ok_type=ok_type)

        elif isinstance(
            type_anno.our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            code = _generate_deserialize_instance_property(prop=prop, ok_type=ok_type)

        else:
            assert_never(type_anno.our_type)
    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert (
            isinstance(type_anno.items, intermediate.PrimitiveTypeAnnotation)
            or isinstance(type_anno.items, intermediate.OurTypeAnnotation)
            and isinstance(
                type_anno.items.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            )
        ), (
            f"NOTE (mristin, 2023-11-10): We expect only lists of classes "
            f"at the moment, but you specified {type_anno}. "
            f"Please contact the developers if you need this feature."
        )

        code = _generate_deserialize_list_property(prop=prop, ok_type=ok_type)
    else:
        assert_never(type_anno)

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        json_prop_literal = cpp_common.string_literal(naming.json_property(prop.name))

        code = Stripped(
            f"""\
if (json.contains({json_prop_literal})) {{
{I}{indent_but_first_line(code, I)}
}}"""
        )

    return code


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_concretely_deserialize_implementation(
    cls: intermediate.ConcreteClass,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """
    Generate the concrete deserialization for the class ``cls``.

    It is assumed that the dispatch has been already effectuated to this generated
    function, so no further dispatch should be performed.
    """
    if cls.is_implementation_specific:
        implementation_key = specific_implementations.ImplementationKey(
            f"jsonization/deserialize_{cls.name}.cpp"
        )

        code = spec_impls.get(implementation_key, None)
        if code is None:
            return None, Error(
                cls.parsed.node,
                f"The implementation is missing for the JSON deserialization "
                f"of {cls.name!r}: {implementation_key}",
            )
        return code, None

    interface_name = cpp_naming.interface_name(cls.name)

    if len(cls.ancestors) == 0:
        # NOTE (mristin, 2023-11-10):
        # We will not need to upcast this instance, so the return value type
        # is simply the interface.
        ok_type = Stripped(f"types::{interface_name}")
    else:
        # NOTE (mristin, 2023-11-10):
        # We have to leave it open to upcast to an ancestor class, and hence
        # we introduce a template parameter.
        ok_type = Stripped("T")

    expected_properties = cpp_naming.constant_name(
        Identifier(f"properties_in_{cls.name}")
    )

    blocks = [
        Stripped(
            f"""\
if (!json.is_object()) {{
{I}std::wstring message = common::Concat(
{II}L"Expected an object, but got: ",
{II}common::Utf8ToWstring(json.type_name())
{I});

{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}common::make_optional<DeserializationError>(
{III}message
{II})
{I});
}}"""
        ),
        Stripped(
            f"""\
if (!additional_properties) {{
{I}for (const auto& key_val : json.items()) {{
{II}auto it(
{III}{expected_properties}.find(key_val.key())
{II});
{II}if (it == {expected_properties}.end()) {{
{III}std::wstring message = common::Concat(
{IIII}L"Unexpected additional property: ",
{IIII}common::Utf8ToWstring(key_val.key())
{III});

{III}return std::make_pair<
{IIII}common::optional<std::shared_ptr<{ok_type}> >,
{IIII}common::optional<DeserializationError>
{III}>(
{IIII}common::nullopt,
{IIII}common::make_optional<DeserializationError>(
{IIIII}message
{IIII})
{III});
{II}}}
{I}}}
}}"""
        ),
    ]  # type: List[Stripped]

    class_name = cpp_naming.class_name(cls.name)

    if len(cls.properties) == 0:
        blocks.append(
            Stripped(
                f"""\
return std::make_pair(
{I}common::make_optional<
{II}std::shared_ptr<{ok_type}>
{I}>(
{II}// NOTE (mristin):
{II}// We deliberately do not use std::make_shared here to avoid an unnecessary
{II}// upcast.
{II}new types::{class_name}()
{I}),
{I}common::nullopt
);"""
            )
        )
    else:
        names_of_required_properties = [
            prop.name
            for prop in cls.properties
            if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
        ]

        if cls.serialization.with_model_type:
            names_of_required_properties.append(Identifier("model_type"))

        if len(names_of_required_properties) > 0:
            blocks.append(Stripped("// region Check required properties"))
            for prop_name in names_of_required_properties:
                json_prop_name = naming.json_property(prop_name)
                json_prop_name_literal = cpp_common.string_literal(json_prop_name)
                blocks.append(
                    Stripped(
                        f"""\
if (!json.contains({json_prop_name_literal})) {{
{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}common::make_optional<DeserializationError>(
{III}L"The required property {json_prop_name} is missing"
{II})
{I});
}}"""
                    )
                )

            blocks.append(Stripped("// endregion Check required properties"))

        # region Initialization
        blocks.append(Stripped("// region Initialization"))

        if len(cls.properties) > 0:
            blocks.append(Stripped("common::optional<DeserializationError> error;"))

        init_statements = []  # type: List[Stripped]

        for prop in cls.properties:
            var_name = cpp_naming.variable_name(Identifier(f"the_{prop.name}"))
            var_type = cpp_common.generate_type(
                type_annotation=prop.type_annotation,
                types_namespace=cpp_common.TYPES_NAMESPACE,
            )

            if not isinstance(
                prop.type_annotation, intermediate.OptionalTypeAnnotation
            ):
                if "\n" in var_type:
                    var_type = Stripped(
                        f"""\
common::optional<
{I}{indent_but_first_line(var_type, I)}
>"""
                    )
                else:
                    if var_type.endswith(">"):
                        var_type = Stripped(f"common::optional<{var_type} >")
                    else:
                        var_type = Stripped(f"common::optional<{var_type}>")

            init_statements.append(Stripped(f"{var_type} {var_name};"))

        blocks.append(Stripped("\n\n".join(init_statements)))

        blocks.append(Stripped("// endregion Initialization"))
        # endregion

        # region Deserialize properties
        for prop in cls.properties:
            json_prop_name = naming.json_property(prop.name)
            blocks.append(Stripped(f"// region De-serialize {json_prop_name}"))

            blocks.append(_generate_deserialize_property(prop=prop, ok_type=ok_type))

            blocks.append(Stripped(f"// endregion De-serialize {json_prop_name}"))
        # endregion

        if cls.serialization.with_model_type:
            # NOTE (mristin):
            # If the serialization requires a model type, we consequently check for it
            # here. The model type thus obtained is *not* used for any dispatch. We only
            # use this value for verification to make sure that the model type
            # of the instances is consistent with the expected value for its concrete
            # class. This will be performed even though the code might have had to parse
            # model type before for the dispatch. We decided to double-check to cover
            # the case where a dispatch is *unnecessary* (*e.g.*, the caller knows the
            # expected runtime type), but the model type might still be invalid in the
            # input. Hence, when the dispatch is *necessary*, the model type JSON
            # property will be parsed twice, which is a cost we currently find
            # acceptable.

            blocks.append(
                Stripped(
                    """\
// region Check model type
// This check is intended only for verification, not for dispatch."""
                )
            )

            model_type = naming.json_model_type(cls.name)

            blocks.append(
                Stripped(
                    f"""\
common::optional<
{I}std::wstring
> model_type;

std::tie(
{I}model_type,
{I}error
) = DeserializeWstring(
{I}json["modelType"]
);

if (error.has_value()) {{
{I}error->path.segments.emplace_front(
{II}common::make_unique<PropertySegment>(
{III}L"modelType"
{II})
{I});

{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}

if (*model_type != L"{model_type}") {{
{I}std::wstring message = common::Concat(
{II}L"Expected model type '{model_type}', "
{II}L"but got: ",
{II}*model_type
{I});

{I}error = common::make_optional<DeserializationError>(
{II}message
{I});

{I}return std::make_pair<
{II}common::optional<std::shared_ptr<{ok_type}> >,
{II}common::optional<DeserializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}"""
                )
            )

            blocks.append(Stripped("// endregion Check model type"))

        # region Pass arguments to the constructor
        property_names = [prop.name for prop in cls.properties]
        constructor_argument_names = [arg.name for arg in cls.constructor.arguments]

        # fmt: off
        assert (
                set(prop.name for prop in cls.properties)
                == set(arg.name for arg in cls.constructor.arguments)
        ), (
            f"Expected the properties to coincide with constructor arguments, "
            f"but they do not for {cls.name!r}:"
            f"{property_names=}, {constructor_argument_names=}"
        )
        # fmt: on

        constructor_args = []  # type: List[Stripped]
        for arg in cls.constructor.arguments:
            prop = cls.properties_by_name[arg.name]

            var_name = cpp_naming.variable_name(Identifier(f"the_{prop.name}"))
            if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
                constructor_args.append(Stripped(f"std::move({var_name})"))
            else:
                constructor_args.append(Stripped(f"std::move(*{var_name})"))

        constructor_args_joined = ",\n".join(constructor_args)

        blocks.append(
            Stripped(
                f"""\
return std::make_pair(
{I}common::make_optional<
{II}std::shared_ptr<{ok_type}>
{I}>(
{II}// NOTE (mristin):
{II}// We deliberately do not use std::make_shared here to avoid an unnecessary
{II}// upcast.
{II}new types::{class_name}(
{III}{indent_but_first_line(constructor_args_joined, III)}
{II})
{I}),
{I}common::nullopt
);"""
            )
        )
        # endregion

    body = "\n\n".join(blocks)

    if len(cls.concrete_descendants) == 0:
        function_name = cpp_naming.function_name(Identifier(f"deserialize_{cls.name}"))
    else:
        function_name = cpp_naming.function_name(
            Identifier(f"concretely_deserialize_{cls.name}")
        )

    if len(cls.ancestors) > 0:
        # NOTE (mristin, 2023-11-10):
        # We have to introduce the template so that we do not have to
        # unnecessarily upcast the instance to ancestor classes.
        prefix = Stripped(
            f"""\
template <
{I}typename T,
{I}typename std::enable_if<
{II}std::is_base_of<T, types::{interface_name}>::value
{I}>::type*
>
std::pair<
{I}common::optional<std::shared_ptr<T> >,
{I}common::optional<DeserializationError>
>"""
        )
    else:
        prefix = Stripped(
            f"""\
std::pair<
{I}common::optional<
{II}std::shared_ptr<types::{interface_name}>
{I}>,
{I}common::optional<DeserializationError>
>"""
        )

    expected_properties_literals = [
        f"{cpp_common.string_literal(naming.json_property(prop.name))}"
        for prop in cls.properties
    ]

    if cls.serialization.with_model_type:
        expected_properties_literals.append(cpp_common.string_literal("modelType"))

    expected_properties_literals_joined = ",\n".join(expected_properties_literals)

    expected_properties_definition = Stripped(
        f"""\
std::set<std::string> {expected_properties} = {{
{I}{indent_but_first_line(expected_properties_literals_joined, I)}
}};"""
    )

    return (
        Stripped(
            f"""\
{expected_properties_definition}

{prefix} {function_name}(
{I}const nlohmann::json& json,
{I}bool additional_properties
) {{
{I}{indent_but_first_line(body, I)}
}}"""
        ),
        None,
    )


@require(
    lambda cls: len(cls.concrete_descendants) > 0,
    "No dispatch possible without concrete descendants",
)
def _generate_dispatch_deserialize_implementation(
    cls: intermediate.ClassUnion,
) -> List[Stripped]:
    """Generate the impl. of the dispatching deserialization function for ``cls``."""
    targets: Iterable[intermediate.ConcreteClass]

    if isinstance(cls, intermediate.ConcreteClass):
        targets = itertools.chain([cls], cls.concrete_descendants)
    else:
        targets = cls.concrete_descendants

    assert targets is not None

    interface_name = cpp_naming.interface_name(cls.name)

    entries = []  # type: List[Stripped]
    for target_cls in targets:
        model_type = naming.json_model_type(target_cls.name)

        if len(target_cls.concrete_descendants) > 0:
            target_function = Stripped(
                cpp_naming.function_name(
                    Identifier(f"concretely_deserialize_{target_cls.name}")
                )
            )
        else:
            target_function = Stripped(
                cpp_naming.function_name(Identifier(f"deserialize_{target_cls.name}"))
            )

        target_function = Stripped(
            f"""\
{target_function}<
{I}types::{interface_name}
>"""
        )

        entries.append(
            Stripped(
                f"""\
{{
{I}{indent_but_first_line(cpp_common.string_literal(model_type), I)},
{I}{indent_but_first_line(target_function, I)}
}}"""
            )
        )

    entries_joined = ",\n".join(entries)

    dispatch_name = cpp_naming.constant_name(
        Identifier(f"deserialize_{cls.name}_by_model_type")
    )

    function_name = cpp_naming.function_name(Identifier(f"deserialize_{cls.name}"))

    return [
        Stripped(
            f"""\
std::map<
{I}std::string,
{I}std::function<
{II}std::pair<
{III}common::optional<std::shared_ptr<types::{interface_name}> >,
{III}common::optional<DeserializationError>
{II}>(const nlohmann::json&, bool)
{I}>
> {dispatch_name} = {{
{I}{indent_but_first_line(entries_joined, I)}
}};"""
        ),
        Stripped(
            f"""\
std::pair<
{I}common::optional<
{II}std::shared_ptr<types::{interface_name}>
{I}>,
{I}common::optional<DeserializationError>
> {function_name}(
{I}const nlohmann::json& json,
{I}bool additional_properties
) {{
{I}const std::string* model_type;
{I}common::optional<DeserializationError> error;

{I}std::tie(
{II}model_type,
{II}error
{I}) = GetModelTypeFrom(json);

{I}if (error.has_value()) {{
{II}return std::make_pair<
{III}common::optional<std::shared_ptr<types::{interface_name}> >,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}std::move(error)
{II});
{I}}}

{I}const auto it = {dispatch_name}.find(*model_type);
{I}if (it == {dispatch_name}.end()) {{
{II}std::wstring message = common::Concat(
{III}L"The dispatch to the JSON de-serialization of "
{III}L"types::{interface_name} "
{III}L"is not defined for model type: ",
{III}common::Utf8ToWstring(*model_type)
{II});

{II}return std::make_pair<
{III}common::optional<std::shared_ptr<types::{interface_name}> >,
{III}common::optional<DeserializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<DeserializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}return (it->second)(json, additional_properties);
}}"""
        ),
    ]


def _generate_deserialization_implementation(cls: intermediate.ClassUnion) -> Stripped:
    """Generate the implementation of ``*From`` function."""
    deserialize_function = _determine_deserialize_function_to_call(cls=cls)

    interface_name = cpp_naming.interface_name(cls.name)

    deserialization_name = cpp_naming.function_name(Identifier(f"{cls.name}_from"))

    return Stripped(
        f"""\
common::expected<
{I}std::shared_ptr<types::{interface_name}>,
{I}DeserializationError
> {deserialization_name}(
{I}const nlohmann::json& json,
{I}bool additional_properties
) {{
{I}common::optional<
{II}std::shared_ptr<types::{interface_name}>
{I}> instance;

{I}common::optional<DeserializationError> error;

{I}std::tie(
{II}instance,
{II}error
{I}) = {indent_but_first_line(deserialize_function, I)}(
{II}json,
{II}additional_properties
{I});

{I}if (instance.has_value()) {{
{II}return std::move(*instance);
{I}}}

{I}if (!error.has_value()) {{
{II}throw std::logic_error(
{III}"Unexpected null error when null instance."
{II});
{I}}}
{I}return common::make_unexpected(
{II}std::move(*error)
{I});
}}"""
    )


def _generate_serialization_exception_implementation() -> List[Stripped]:
    """Generate the implementation of the ``SerializationException``."""
    return [
        Stripped("// region SerializationException"),
        Stripped(
            f"""\
std::string RenderSerializationErrorMessage(
{I}const std::wstring& cause,
{I}const iteration::Path& path
) {{
{I}return common::WstringToUtf8(
{II}common::Concat(
{III}L"Serialization failed at ",
{III}path.ToWstring(),
{III}L": ",
{III}cause
{II})
{I});
}}"""
        ),
        Stripped(
            f"""\
SerializationException::SerializationException(
{I}std::wstring cause,
{I}iteration::Path path
) :
{I}cause_(std::move(cause)),
{I}path_(std::move(path)),
{I}msg_(RenderSerializationErrorMessage(cause, path)) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
const char* SerializationException::what() const noexcept {{
{I}return msg_.c_str();
}}"""
        ),
        Stripped(
            f"""\
const std::wstring& SerializationException::cause() const noexcept {{
{I}return cause_;
}}"""
        ),
        Stripped(
            f"""\
const iteration::Path& SerializationException::path() const noexcept {{
{I}return path_;
}}"""
        ),
        Stripped("// endregion SerializationException"),
    ]


def _generate_serialize_int() -> Stripped:
    """Generate the function to serialize an integer to a JSON value."""
    return Stripped(
        f"""\
/**
 * \\brief Serialize the given number to a JSON value.
 *
 * We verify that the integer is within the range representable by 64-bit floats
 * for interoperability with other de-serializers.
 */
std::pair<
{I}common::optional<nlohmann::json>,
{I}common::optional<SerializationError>
> SerializeInt64(int64_t value) {{
{I}if (
{II}value < -9007199254740991L
{II}|| value > 9007199254740991L
{I}) {{
{II}const std::wstring message = common::Concat(
{III}L"The integer ",
{III}std::to_wstring(value),
{III}L" can not be serialized to JSON "
{III}L"as it is outside the range [-2^53 + 1, 2^53 - 1] and can not "
{III}L"be exactly represented as a 64-bit floating point number."
{II});

{II}return std::make_pair<
{III}common::optional<nlohmann::json>,
{III}common::optional<SerializationError>
{II}>(
{III}common::nullopt,
{III}common::make_optional<SerializationError>(
{IIII}message
{III})
{II});
{I}}}

{I}return std::make_pair<
{II}common::optional<nlohmann::json>,
{II}common::optional<SerializationError>
{I}>(
{II}common::make_optional<nlohmann::json>(value),
{II}common::nullopt
{I});
}}"""
    )


def _generate_serialize_str() -> Stripped:
    """Generate the function to serialize a wide string to a JSON value."""
    return Stripped(
        f"""\
/**
 * Serialize the given text to a JSON value.
 */
nlohmann::json SerializeWstring(
{I}const std::wstring& text
) {{
{I}return nlohmann::json(
{II}common::WstringToUtf8(text)
{I});
}}"""
    )


def _generate_serialize_bytearray() -> Stripped:
    """Generate the function to serialize a byte array to a JSON value."""
    return Stripped(
        f"""\
/**
 * Serialize the given bytes to a JSON value.
 */
nlohmann::json SerializeByteArray(
{I}const std::vector<std::uint8_t>& bytes
) {{
{I}return nlohmann::json(
{II}std::move(
{III}stringification::Base64Encode(bytes)
{II})
{I});
}}"""
    )


def _generate_serialize_iclass_definition() -> Stripped:
    """Generate the definition of the main dispatch for serializing ``IClass``."""
    return Stripped(
        f"""\
std::pair<
{I}common::optional<nlohmann::json>,
{I}common::optional<SerializationError>
> SerializeIClass(
{I}const types::IClass& that
);"""
    )


def _generate_serialize_primitive_property(
    getter_expr: str,
    primitive_type: intermediate.PrimitiveType,
    property_name: Identifier,
) -> Stripped:
    """
    Generate the snippet to serialize the given primitive property.

    The ``getter_expr`` refers to the C++ expression specifying the value
    to be serialized.

    The ``property_name`` refers to the intermediate property name.
    """
    json_prop_name_literal = cpp_common.string_literal(
        naming.json_property(property_name)
    )

    if primitive_type is intermediate.PrimitiveType.BOOL:
        return Stripped(f"result[{json_prop_name_literal}] = {getter_expr};")

    elif primitive_type is intermediate.PrimitiveType.INT:
        serialized_var = cpp_naming.variable_name(Identifier(f"json_{property_name}"))
        return Stripped(
            f"""\
common::optional<nlohmann::json> {serialized_var};
std::tie(
{I}{serialized_var},
{I}error
) = SerializeInt64(
{I}{indent_but_first_line(getter_expr, I)}
);
if (error.has_value()) {{
{I}error->path.segments.emplace_front(
{II}common::make_unique<iteration::PropertySegment>(
{III}iteration::Property::{cpp_naming.enum_literal_name(property_name)}
{II})
{I});

{I}return std::make_pair<
{II}common::optional<nlohmann::json>,
{II}common::optional<SerializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}

result[{json_prop_name_literal}] = std::move(
{I}{serialized_var}
);"""
        )
    elif primitive_type is intermediate.PrimitiveType.FLOAT:
        return Stripped(
            f"""\
result[{json_prop_name_literal}] = {getter_expr};"""
        )

    elif primitive_type is intermediate.PrimitiveType.STR:
        serialized_var = cpp_naming.variable_name(Identifier(f"json_{property_name}"))
        return Stripped(
            f"""\
result[{json_prop_name_literal}] = SerializeWstring(
{I}{indent_but_first_line(getter_expr, II)}
);"""
        )

    elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
        return Stripped(
            f"""\
result[{json_prop_name_literal}] = stringification::Base64Encode(
{I}{getter_expr}
);"""
        )
    else:
        assert_never(primitive_type)


def _generate_serialize_property(prop: intermediate.Property) -> Stripped:
    """Generate the code snippet to serialize the property ``prop``."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    code = None  # type: Optional[Stripped]

    getter = cpp_naming.getter_name(prop.name)
    maybe_var = None
    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        maybe_var = cpp_naming.variable_name(Identifier(f"maybe_{prop.name}"))
        getter_expr = f"*{maybe_var}"
    else:
        getter_expr = f"that.{getter}()"

    json_prop_name = naming.json_property(prop.name)

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        code = _generate_serialize_primitive_property(
            getter_expr=getter_expr,
            primitive_type=type_anno.a_type,
            property_name=prop.name,
        )

    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        if isinstance(type_anno.our_type, intermediate.Enumeration):
            code = Stripped(
                f"""\
result[{cpp_common.string_literal(json_prop_name)}] = stringification::to_string(
{I}{indent_but_first_line(getter_expr, I)}
);"""
            )
        elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
            code = _generate_serialize_primitive_property(
                getter_expr=getter_expr,
                primitive_type=type_anno.our_type.constrainee,
                property_name=prop.name,
            )
        elif isinstance(
            type_anno.our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            serialized_var = cpp_naming.variable_name(Identifier(f"json_{prop.name}"))

            code = Stripped(
                f"""\
common::optional<nlohmann::json> {serialized_var};
std::tie(
{I}{serialized_var},
{I}error
) = SerializeIClass(
{I}*{indent_but_first_line(getter_expr, I)}
);
if (error.has_value()) {{
{I}error->path.segments.emplace_front(
{II}common::make_unique<iteration::PropertySegment>(
{III}iteration::Property::{cpp_naming.enum_literal_name(prop.name)}
{II})
{I});

{I}return std::make_pair<
{II}common::optional<nlohmann::json>,
{II}common::optional<SerializationError>
{I}>(
{II}common::nullopt,
{II}std::move(error)
{I});
}}

result[{cpp_common.string_literal(json_prop_name)}] = std::move(
{I}*{serialized_var}
);"""
            )
        else:
            assert_never(type_anno.our_type)
    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert (
            isinstance(type_anno.items, intermediate.PrimitiveTypeAnnotation)
            or isinstance(type_anno.items, intermediate.OurTypeAnnotation)
            and isinstance(
                type_anno.items.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            )
        ), (
            f"NOTE (mristin, 2023-11-21): We expect only lists of classes "
            f"at the moment, but you specified {type_anno}. "
            f"Please contact the developers if you need this feature."
        )

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            assert maybe_var is not None
            size_expr = f"{maybe_var}->size()"
        else:
            size_expr = f"that.{getter}().size()"

        serialized_var = cpp_naming.variable_name(Identifier(f"json_{prop.name}"))

        const_ref_item_type = cpp_common.generate_type_with_const_ref_if_applicable(
            type_annotation=type_anno.items, types_namespace=cpp_common.TYPES_NAMESPACE
        )

        index_var = cpp_naming.variable_name(Identifier(f"index_{prop.name}"))
        code = Stripped(
            f"""\
nlohmann::json {serialized_var} = nlohmann::json::array();
{serialized_var}.get_ptr<nlohmann::json::array_t*>()->reserve(
{I}{indent_but_first_line(size_expr, I)}
);
size_t {index_var} = 0;
for (
{I}{const_ref_item_type} item
{I}: {getter_expr}
) {{
{I}common::optional<nlohmann::json> json_item;
{I}std::tie(
{II}json_item,
{II}error
{I}) = SerializeIClass(*item);

{I}if (error.has_value()) {{
{II}error->path.segments.emplace_front(
{III}common::make_unique<iteration::IndexSegment>(
{IIII}{index_var}
{III})
{II});

{II}error->path.segments.emplace_front(
{III}common::make_unique<iteration::PropertySegment>(
{IIII}iteration::Property::{cpp_naming.enum_literal_name(prop.name)}
{III})
{II});

{II}return std::make_pair<
{III}common::optional<nlohmann::json>,
{III}common::optional<SerializationError>
{II}>(
{III}common::nullopt,
{III}std::move(error)
{II});
{I}}}

{I}{serialized_var}.emplace_back(
{II}std::move(*json_item)
{I});

{I}++{index_var};
}}
result[{cpp_common.string_literal(json_prop_name)}] = std::move(
{I}{serialized_var}
);"""
        )
    else:
        assert_never(type_anno)

    assert code is not None

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        maybe_var_type = cpp_common.generate_type_with_const_ref_if_applicable(
            type_annotation=prop.type_annotation,
            types_namespace=cpp_common.TYPES_NAMESPACE,
        )

        assert maybe_var is not None

        code = Stripped(
            f"""\
{maybe_var_type} {maybe_var}(
{I}that.{getter}()
);
if ({maybe_var}.has_value()) {{
{I}{indent_but_first_line(code, I)}
}}"""
        )

    return code


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_serialize_cls(
    cls: intermediate.ConcreteClass,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the serialization function for the class ``cls``."""
    if cls.is_implementation_specific:
        implementation_key = specific_implementations.ImplementationKey(
            f"jsonization/serialize_{cls.name}.cpp"
        )

        code = spec_impls.get(implementation_key, None)
        if code is None:
            return None, Error(
                cls.parsed.node,
                f"The implementation is missing for the JSON serialization "
                f"of {cls.name!r}: {implementation_key}",
            )
        return code, None

    blocks = [
        Stripped(
            """\
nlohmann::json result = nlohmann::json::object();"""
        )
    ]  # type: List[Stripped]

    needs_error = False
    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)
        primitive_type = intermediate.try_primitive_type(type_anno)

        if primitive_type is not None and (
            primitive_type is intermediate.PrimitiveType.INT
        ):
            needs_error = True
            break

        if isinstance(type_anno, intermediate.OurTypeAnnotation) or (
            isinstance(type_anno, intermediate.ListTypeAnnotation)
            and isinstance(type_anno.items, intermediate.OurTypeAnnotation)
        ):
            needs_error = True
            break

    if needs_error:
        blocks.append(Stripped("common::optional<SerializationError> error;"))

    for prop in cls.properties:
        blocks.append(_generate_serialize_property(prop=prop))

    if cls.serialization.with_model_type:
        model_type_literal = cpp_common.string_literal(naming.json_model_type(cls.name))
        blocks.append(Stripped(f'result["modelType"] = {model_type_literal};'))

    blocks.append(
        Stripped(
            f"""\
return std::make_pair<
{I}common::optional<nlohmann::json>,
{I}common::optional<SerializationError>
>(
{I}common::make_optional<nlohmann::json>(std::move(result)),
{I}common::nullopt
);"""
        )
    )

    blocks_joined = "\n\n".join(blocks)

    serialize_name = cpp_naming.function_name(Identifier(f"serialize_{cls.name}"))

    interface_name = cpp_naming.interface_name(cls.name)

    return (
        Stripped(
            f"""\
std::pair<
{I}common::optional<nlohmann::json>,
{I}common::optional<SerializationError>
> {serialize_name}(
{I}const types::{interface_name}& that
) {{
{I}{indent_but_first_line(blocks_joined, I)}
}}"""
        ),
        None,
    )


def _generate_serialize_iclass_implementation(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the main dispatch function for serializing ``IClass``."""
    case_blocks = []  # type: List[Stripped]
    for cls in symbol_table.concrete_classes:
        serialize_name = cpp_naming.function_name(Identifier(f"serialize_{cls.name}"))

        model_type_literal = cpp_naming.enum_literal_name(cls.name)
        model_type_enum = cpp_naming.enum_name(Identifier("Model_type"))

        interface_name = cpp_naming.interface_name(cls.name)

        case_blocks.append(
            Stripped(
                f"""\
case types::{model_type_enum}::{model_type_literal}:
{I}return {serialize_name}(
{II}dynamic_cast<const types::{interface_name}&>(that)
{I});"""
            )
        )

    case_blocks.append(
        Stripped(
            f"""\
default: {{
{I}std::string message = common::Concat(
{II}"Unexpected model type: ",
{II}std::to_string(
{III}static_cast<std::uint32_t>(
{IIII}that.model_type()
{III})
{II})
{I});

{I}throw std::invalid_argument(message);
}}"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    return Stripped(
        f"""\
std::pair<
{I}common::optional<nlohmann::json>,
{I}common::optional<SerializationError>
> SerializeIClass(
{I}const types::IClass& that
) {{
{I}switch (that.model_type()) {{
{II}{indent_but_first_line(case_blocks_joined, II)}
{I}}};
}}"""
    )


def _generate_serialize_implementation() -> Stripped:
    """Generate the main serialization function."""
    return Stripped(
        f"""\
nlohmann::json Serialize(
{I}const types::IClass& that
) {{
{I}common::optional<nlohmann::json> result;
{I}common::optional<SerializationError> error;

{I}std::tie(
{II}result,
{II}error
{I}) = SerializeIClass(that);

{I}if (error.has_value()) {{
{II}throw SerializationException(
{III}std::move(error->cause),
{III}std::move(error->path)
{II});
{I}}}

{I}return std::move(*result);
}}"""
    )


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate_implementation(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
    library_namespace: Stripped,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the C++ implementation of the de/serialization functions."""
    namespace = Stripped(f"{library_namespace}::{cpp_common.JSONIZATION_NAMESPACE}")

    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            f"""\
#include "{include_prefix_path}/jsonization.hpp"
#include "{include_prefix_path}/stringification.hpp"
#include "{include_prefix_path}/wstringification.hpp"

#pragma warning(push, 0)
#include <functional>
#include <map>
#include <set>
#include <sstream>
#pragma warning(pop)"""
        ),
        cpp_common.generate_namespace_opening(namespace),
        *_generate_property_segment_implementation(),
        *_generate_index_segment_implementation(),
        *_generate_path_implementation(),
        Stripped("// region De-serialization"),
        *_generate_deserialization_error_implementation(),
        _generate_deserialize_bool(),
        _generate_deserialize_int(),
        _generate_deserialize_float(),
        _generate_deserialize_str(),
        _generate_deserialize_bytearray(),
        _generate_get_model_type(),
    ]

    for cls in symbol_table.classes:
        if isinstance(cls, intermediate.ConcreteClass):
            blocks.append(
                _generate_concretely_deserialize_definition(
                    cls=cls,
                )
            )

        if len(cls.concrete_descendants) > 0:
            blocks.append(_generate_dispatch_deserialize_definition(cls=cls))

    errors = []  # type: List[Error]

    for cls in symbol_table.classes:
        if isinstance(cls, intermediate.ConcreteClass):
            deserialize_block, error = _generate_concretely_deserialize_implementation(
                cls=cls,
                spec_impls=spec_impls,
            )
            if error is not None:
                errors.append(error)
                continue

            assert deserialize_block is not None
            blocks.append(deserialize_block)

        if len(cls.concrete_descendants) > 0:
            deserialize_dispatch_blocks = _generate_dispatch_deserialize_implementation(
                cls=cls
            )
            blocks.extend(deserialize_dispatch_blocks)

    for cls in symbol_table.classes:
        blocks.append(_generate_deserialization_implementation(cls=cls))

    blocks.extend(
        [
            Stripped("// endregion De-serialization"),
            Stripped("// region Serialization"),
            Stripped(
                f"""\
/**
 * \\brief Represent a serialization error.
 *
 * We use this error internally to avoid unnecessary stack unwinding,
 * but throw the \\ref SerializationException at the final site of
 * the serialization for the user.
 */
struct SerializationError {{
{I}/**
{I} * Human-readable description of the error
{I} */
{I}std::wstring cause;

{I}/**
{I} * Path to the value that caused the error
{I} */
{I}iteration::Path path;

{I}explicit SerializationError(
{II}std::wstring a_cause
{I}) : cause(std::move(a_cause)) {{
{II}// Intentionally empty.
{I}}}
}};  // struct SerializationError"""
            ),
            *_generate_serialization_exception_implementation(),
            _generate_serialize_int(),
            _generate_serialize_str(),
            _generate_serialize_bytearray(),
            _generate_serialize_iclass_definition(),
        ]
    )

    for cls in symbol_table.concrete_classes:
        serialize_block, error = _generate_serialize_cls(cls=cls, spec_impls=spec_impls)
        if error is not None:
            errors.append(error)
        else:
            assert serialize_block is not None
            blocks.append(serialize_block)

    blocks.append(_generate_serialize_iclass_implementation(symbol_table=symbol_table))

    blocks.append(_generate_serialize_implementation())

    blocks.extend(
        [
            Stripped("// endregion Serialization"),
            cpp_common.generate_namespace_closing(namespace),
            cpp_common.WARNING,
        ]
    )

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue(), None
