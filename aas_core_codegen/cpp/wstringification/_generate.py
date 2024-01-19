"""Generate C++ code to de/wstringify enumerations and primitives."""

import io
from typing import List

from icontract import ensure

import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Stripped, Identifier, indent_but_first_line
from aas_core_codegen.cpp import (
    common as cpp_common,
    naming as cpp_naming,
)
from aas_core_codegen.cpp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
)


def _generate_model_type_from_wstring_definition() -> List[Stripped]:
    """Generate the definition of translation of a model type from wstring."""
    enum_name = cpp_naming.enum_name(Identifier("Model_type"))
    from_wstring = cpp_naming.function_name(Identifier("model_type_from_wstring"))
    must_from_wstring = cpp_naming.function_name(
        Identifier("must_model_type_from_wstring")
    )

    return [
        Stripped(
            f"""\
/**
 * Try to parse the \\p text as a model type literal.
 *
 * \\param text to be parsed
 * \\return literal, or nothing, if \\p text invalid
 */
common::optional<types::{enum_name}> {from_wstring}(
{I}const std::wstring& text
);"""
        ),
        Stripped(
            f"""\
/**
 * Parse the \\p text as a model type literal.
 *
 * \\param text to be parsed
 * \\return literal
 * \\throw std::invalid_argument if \\p text invalid
 */
types::{enum_name} {must_from_wstring}(
{I}const std::wstring& text
);"""
        ),
    ]


def _generate_model_type_from_wstring_implementation(
    symbol_table: intermediate.SymbolTable,
) -> List[Stripped]:
    """Generate the implementation of translation of a model type from wstring."""
    blocks = []  # type: List[Stripped]

    # region Map

    enum_name = cpp_naming.enum_name(Identifier("Model_type"))

    items = []  # type: List[str]
    for cls in symbol_table.concrete_classes:
        literal_name = cpp_naming.enum_literal_name(cls.name)

        literal_value = cpp_common.wstring_literal(
            aas_core_codegen.naming.json_model_type(cls.name)
        )

        items.append(
            Stripped(
                f"""\
{{
{I}{literal_value},
{I}types::{enum_name}::{literal_name}
}}"""
            )
        )

    map_name = cpp_naming.constant_name(Identifier("model_type_from_wstring_map"))

    items_joined = ",\n".join(items)

    blocks.append(
        Stripped(
            f"""\
const std::unordered_map<
{I}std::wstring,
{I}types::{enum_name}
> {map_name} = {{
{I}{indent_but_first_line(items_joined, I)}
}};"""
        )
    )

    # endregion

    # region From function

    from_wstring = cpp_naming.function_name(Identifier("model_type_from_wstring"))

    blocks.append(
        Stripped(
            f"""\
common::optional<types::{enum_name}> {from_wstring}(
{I}const std::wstring& text
) {{
{I}const auto it = {map_name}.find(
{II}text
{I});
{I}if (it == {map_name}.end()) {{
{II}return {{}};
{I}}}
{I}return it->second;
}}"""
        )
    )

    # endregion

    # region Must-from function

    must_from_wstring = cpp_naming.function_name(
        Identifier("must_model_type_from_wstring")
    )

    blocks.append(
        Stripped(
            f"""\
types::{enum_name} {must_from_wstring}(
{I}const std::wstring& text
) {{
{I}const auto it = {map_name}.find(
{II}text
{I});
{I}if (it == {map_name}.end()) {{
{II}throw std::invalid_argument(
{III}common::WstringToUtf8(
{IIII}common::Concat(
{IIIII}L"Unexpected model type literal: ",
{IIIII}text
{IIII})
{III})
{II});
{I}}}
{I}return it->second;
}}"""
        )
    )

    # endregion

    return blocks


def _generate_model_type_to_wstring_definition() -> Stripped:
    """Generate the definition for translating a wstring to a model type."""
    enum_name = cpp_naming.enum_name(Identifier("Model_type"))

    model_type_arg = cpp_naming.argument_name(Identifier("model_type"))

    # NOTE (mristin, 2023-07-12):
    # We use ``to_wstring`` naming to resemble the functions in standard library.
    return Stripped(
        f"""\
/**
 * Translate the enumeration literal \\p {model_type_arg} to text.
 *
 * \\param {model_type_arg} to be converted into text
 * \\return text representation of \\p {model_type_arg}
 * \\throw std::invalid_argument if \\p {model_type_arg} invalid
 */
std::wstring to_wstring(
{I}types::{enum_name} {model_type_arg}
);"""
    )


def _generate_model_type_to_wstring_implementation(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the implementation for translating a wstring to a model type."""
    enum_name = cpp_naming.enum_name(Identifier("Model_type"))

    case_blocks = []  # type: List[Stripped]
    for cls in symbol_table.concrete_classes:
        literal_name = cpp_naming.enum_literal_name(cls.name)
        literal_value = cpp_common.wstring_literal(
            aas_core_codegen.naming.json_model_type(cls.name)
        )

        case_blocks.append(
            Stripped(
                f"""\
case types::{enum_name}::{literal_name}:
return {literal_value};"""
            )
        )

    model_type_arg = cpp_naming.argument_name(Identifier("model_type"))

    case_blocks.append(
        Stripped(
            f"""\
default:
{I}throw std::invalid_argument(
{II}common::Concat(
{III}"Unexpected model type: ",
{III}std::to_string(
{IIII}static_cast<std::uint32_t>({model_type_arg})
{III})
{II})
{I});"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    # NOTE (mristin, 2023-07-12):
    # We use ``to_wstring`` naming to resemble the functions in standard library.
    return Stripped(
        f"""\
std::wstring to_wstring(
{I}types::{enum_name} {model_type_arg}
) {{
{I}switch ({model_type_arg}) {{
{II}{indent_but_first_line(case_blocks_joined, II)}
{I}}}
}}"""
    )


def _generate_enum_from_wstring_definition(
    enum: intermediate.Enumeration,
) -> List[Stripped]:
    """Generate the definition of translation of an enum from wstring."""
    enum_name = cpp_naming.enum_name(enum.name)
    from_wstring = cpp_naming.function_name(Identifier(f"{enum.name}_from_wstring"))
    must_from_wstring = cpp_naming.function_name(
        Identifier(f"must_{enum.name}_from_wstring")
    )

    return [
        Stripped(
            f"""\
/**
 * Try to parse the \\p text as a literal of
 * types::{enum_name}.
 *
 * \\param text to be parsed
 * \\return literal, or nothing, if \\p text invalid
 */
common::optional<types::{enum_name}> {from_wstring}(
{I}const std::wstring& text
);"""
        ),
        Stripped(
            f"""\
/**
 * Parse the \\p text as a literal of
 * types::{enum_name}.
 *
 * \\param text to be parsed
 * \\return literal
 * \\throw std::invalid_argument if \\p text invalid
 */
types::{enum_name} {must_from_wstring}(
{I}const std::wstring& text
);"""
        ),
    ]


def _generate_enum_from_wstring_implementation(
    enum: intermediate.Enumeration,
) -> List[Stripped]:
    """Generate the implementation of translation of an  enum from wstring."""
    blocks = []  # type: List[Stripped]

    # region Map

    enum_name = cpp_naming.enum_name(enum.name)

    items = []  # type: List[str]
    for literal in enum.literals:
        literal_name = cpp_naming.enum_literal_name(literal.name)
        literal_value = cpp_common.wstring_literal(literal.value)

        items.append(
            Stripped(
                f"""\
{{
{I}{literal_value},
{I}types::{enum_name}::{literal_name}
}}"""
            )
        )

    map_name = cpp_naming.constant_name(Identifier(f"{enum.name}_from_wstring_map"))

    items_joined = ",\n".join(items)

    blocks.append(
        Stripped(
            f"""\
const std::unordered_map<
{I}std::wstring,
{I}types::{enum_name}
> {map_name} = {{
{I}{indent_but_first_line(items_joined, I)}
}};"""
        )
    )

    # endregion

    # region From function

    from_wstring = cpp_naming.function_name(Identifier(f"{enum.name}_from_wstring"))

    blocks.append(
        Stripped(
            f"""\
common::optional<types::{enum_name}> {from_wstring}(
{I}const std::wstring& text
) {{
{I}const auto it = {map_name}.find(
{II}text
{I});
{I}if (it == {map_name}.end()) {{
{II}return {{}};
{I}}}
{I}return it->second;
}}"""
        )
    )

    # endregion

    # region Must-from function

    must_from_wstring = cpp_naming.function_name(
        Identifier(f"must_{enum.name}_from_wstring")
    )

    blocks.append(
        Stripped(
            f"""\
types::{enum_name} {must_from_wstring}(
{I}const std::wstring& text
) {{
{I}const auto it = {map_name}.find(
{II}text
{I});
{I}if (it == {map_name}.end()) {{
{II}throw std::invalid_argument(
{III}common::WstringToUtf8(
{IIII}common::Concat(
{IIIII}L"Unexpected model type literal: ",
{IIIII}text
{IIII})
{III})
{II});
{I}}}
{I}return it->second;
}}"""
        )
    )

    # endregion

    return blocks


def _generate_enum_to_wstring_definition(enum: intermediate.Enumeration) -> Stripped:
    """Generate the definition for translating a wstring to an enum literal."""
    enum_name = cpp_naming.enum_name(enum.name)

    literal_arg = cpp_naming.argument_name(Identifier("literal"))

    # NOTE (mristin, 2023-07-12):
    # We use ``to_wstring`` naming to resemble the functions in standard library.
    return Stripped(
        f"""\
/**
 * Translate the enumeration literal \\p {literal_arg}
 * of types::{enum_name} to text.
 *
 * \\param {literal_arg} to be converted into text
 * \\return text representation of \\p {literal_arg}
 * \\throw std::invalid_argument if \\p {literal_arg} invalid
 */
std::wstring to_wstring(
{I}types::{enum_name} {literal_arg}
);"""
    )


def _generate_enum_to_wstring_implementation(
    enum: intermediate.Enumeration,
) -> Stripped:
    """Generate the implementation for translating a wstring to an enum literal."""
    enum_name = cpp_naming.enum_name(enum.name)

    case_blocks = []  # type: List[Stripped]
    for literal in enum.literals:
        literal_name = cpp_naming.enum_literal_name(literal.name)
        literal_value = cpp_common.wstring_literal(literal.value)

        case_blocks.append(
            Stripped(
                f"""\
case types::{enum_name}::{literal_name}:
{I}return {literal_value};"""
            )
        )

    literal_arg = cpp_naming.argument_name(Identifier("literal"))

    case_blocks.append(
        Stripped(
            f"""\
default:
{I}throw std::invalid_argument(
{II}common::Concat(
{III}"Unexpected literal: ",
{III}std::to_string(
{IIII}static_cast<std::uint32_t>({literal_arg})
{III})
{II})
{I});"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    # NOTE (mristin, 2023-07-12):
    # We use ``to_wstring`` naming to resemble the functions in standard library.
    return Stripped(
        f"""\
std::wstring to_wstring(
{I}types::{enum_name} {literal_arg}
) {{
{I}switch ({literal_arg}) {{
{II}{indent_but_first_line(case_blocks_joined, II)}
{I}}}
}}"""
    )


def _generate_base64_encode_definition() -> Stripped:
    """Generate the definition of a stringification of bytes as base64 wstring."""
    function_name = cpp_naming.function_name(Identifier("base64_encode"))
    return Stripped(
        f"""\
/**
 * Encode the \\p bytes with base64 to a std::wstring.
 *
 * \\param bytes to be encoded
 * \\return base64-encoding of \\p bytes
 */
std::wstring {function_name}(
{I}const std::vector<std::uint8_t>& bytes
);"""
    )


def _generate_base64_encode_implementation() -> List[Stripped]:
    """Generate the implementation of a stringification of bytes as base64 wstring."""
    function_name = cpp_naming.function_name(Identifier("base64_encode"))

    wchar_base64_table = cpp_naming.constant_name(Identifier("wchar_base64_table"))

    return [
        Stripped(
            """\
// The following encoder has been adapted from Jouni Malinen <j@w1.fi> to work with
// std::wstring. The original source code is available at:
// https://web.mit.edu/freebsd/head/contrib/wpa/src/utils/base64.c"""
        ),
        Stripped(
            f"""\
static const wchar_t {wchar_base64_table}[65](
{I}L"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
);"""
        ),
        Stripped(
            f"""\
std::wstring {function_name}(
{I}const std::vector<std::uint8_t>& bytes
) {{
{I}// See: https://cplusplus.com/reference/vector/vector/data/.
{I}// The data is guaranteed to be a continuous block in memory.
{I}const unsigned char* src(
{II}bytes.data()
{I});

{I}const std::size_t len = bytes.size();

{I}// 3-byte blocks to 4-byte
{I}const std::size_t olen = 4 * ((len + 2) / 3);

{I}// Integer overflow?
{I}if (olen < len) {{
{II}throw std::invalid_argument(
{III}common::Concat(
{IIII}"The calculation of the output length overflowed. "
{IIII}"The length was: ",
{IIII}std::to_string(len),
{IIII}", but the output length was calculated as: ",
{IIII}std::to_string(olen)
{III})
{II});
{I}}}

{I}std::wstring out_wstring;
{I}out_wstring.resize(olen);

{I}wchar_t* out(
{II}static_cast<wchar_t*>(
{III}&out_wstring[0]
{II})
{I});

{I}const unsigned char* end = src + len;

{I}const unsigned char* in = src;
{I}wchar_t* pos = out;

{I}while (end - in >= 3) {{
{II}*pos++ = {wchar_base64_table}[in[0] >> 2];
{II}*pos++ = {wchar_base64_table}[((in[0] & 0x03) << 4) | (in[1] >> 4)];
{II}*pos++ = {wchar_base64_table}[((in[1] & 0x0f) << 2) | (in[2] >> 6)];
{II}*pos++ = {wchar_base64_table}[in[2] & 0x3f];
{II}in += 3;
{I}}}

{I}if (end - in) {{
{II}*pos++ = {wchar_base64_table}[in[0] >> 2];

{II}if (end - in == 1) {{
{III}*pos++ = {wchar_base64_table}[(in[0] & 0x03) << 4];
{III}*pos++ = L'=';
{II}}} else {{
{III}*pos++ = {wchar_base64_table}[
{IIII}((in[0] & 0x03) << 4) | (in[1] >> 4)
{III}];
{III}*pos++ = {wchar_base64_table}[(in[1] & 0x0f) << 2];
{II}}}
{II}*pos++ = L'=';
{I}}}

{I}return out_wstring;
}}"""
        ),
    ]


# NOTE (mristin, 2023-07-12):
# The SDK does not use base64-decoding *from* wide strings, so we omit that direction
# here following YAGNI.

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
    """Generate the C++ header code for stringification."""
    namespace = Stripped(f"{library_namespace}::wstringification")

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
#include "{include_prefix_path}/types.hpp"

#pragma warning(push, 0)
#include <string>
#include <vector>
#pragma warning(pop)"""
        ),
        cpp_common.generate_namespace_opening(library_namespace),
        Stripped(
            """\
/**
 * \\defgroup wstringification De/wstringify to and from wstrings (where applicable).
 * @{
 */
namespace wstringification {"""
        ),
        *_generate_model_type_from_wstring_definition(),
        _generate_model_type_to_wstring_definition(),
    ]

    for enum in symbol_table.enumerations:
        blocks.extend(_generate_enum_from_wstring_definition(enum=enum))
        blocks.append(_generate_enum_to_wstring_definition(enum=enum))

    blocks.extend(
        [
            _generate_base64_encode_definition(),
            Stripped(
                """\
}  // namespace wstringification
/**@}*/"""
            ),
            cpp_common.generate_namespace_closing(library_namespace),
            cpp_common.WARNING,
            Stripped(f"#endif  // {include_guard_var}"),
        ]
    )

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


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
    """Generate the C++ code for stringification."""
    namespace = Stripped(f"{library_namespace}::wstringification")

    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            f"""\
#include "{include_prefix_path}/wstringification.hpp"

#pragma warning(push, 0)
#include <unordered_map>
#pragma warning(pop)"""
        ),
        cpp_common.generate_namespace_opening(namespace),
        *_generate_model_type_from_wstring_implementation(symbol_table=symbol_table),
        _generate_model_type_to_wstring_implementation(symbol_table=symbol_table),
    ]  # type: List[Stripped]

    for enum in symbol_table.enumerations:
        blocks.extend(_generate_enum_from_wstring_implementation(enum=enum))
        blocks.append(_generate_enum_to_wstring_implementation(enum=enum))

    blocks.extend(
        [
            *_generate_base64_encode_implementation(),
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

    return writer.getvalue()
