"""Generate C++ code to de/stringify enumerations and primitives."""

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


def _generate_model_type_from_string_definition() -> List[Stripped]:
    """Generate the definition of translation of a model type from string."""
    enum_name = cpp_naming.enum_name(Identifier("Model_type"))
    from_string = cpp_naming.function_name(Identifier("model_type_from_string"))
    must_from_string = cpp_naming.function_name(
        Identifier("must_model_type_from_string")
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
common::optional<types::{enum_name}> {from_string}(
{I}const std::string& text
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
types::{enum_name} {must_from_string}(
{I}const std::string& text
);"""
        ),
    ]


def _generate_model_type_from_string_implementation(
    symbol_table: intermediate.SymbolTable,
) -> List[Stripped]:
    """Generate the implementation of translation of a model type from string."""
    blocks = []  # type: List[Stripped]

    # region Map

    enum_name = cpp_naming.enum_name(Identifier("Model_type"))

    items = []  # type: List[str]
    for cls in symbol_table.concrete_classes:
        literal_name = cpp_naming.enum_literal_name(cls.name)

        literal_value = cpp_common.string_literal(
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

    map_name = cpp_naming.constant_name(Identifier("model_type_from_string_map"))

    items_joined = ",\n".join(items)

    blocks.append(
        Stripped(
            f"""\
const std::unordered_map<
{I}std::string,
{I}types::{enum_name}
> {map_name} = {{
{I}{indent_but_first_line(items_joined, I)}
}};"""
        )
    )

    # endregion

    # region From function

    from_string = cpp_naming.function_name(Identifier("model_type_from_string"))

    blocks.append(
        Stripped(
            f"""\
common::optional<types::{enum_name}> {from_string}(
{I}const std::string& text
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

    must_from_string = cpp_naming.function_name(
        Identifier("must_model_type_from_string")
    )

    blocks.append(
        Stripped(
            f"""\
types::{enum_name} {must_from_string}(
{I}const std::string& text
) {{
{I}const auto it = {map_name}.find(
{II}text
{I});
{I}if (it == {map_name}.end()) {{
{II}throw std::invalid_argument(
{III}common::Concat(
{IIII}"Unexpected {enum_name} literal: ",
{IIII}text
{III})
{II});
{I}}}
{I}return it->second;
}}"""
        )
    )

    # endregion

    return blocks


def _generate_model_type_to_string_definition() -> Stripped:
    """Generate the definition for translating a string to a model type."""
    enum_name = cpp_naming.enum_name(Identifier("Model_type"))

    model_type_arg = cpp_naming.argument_name(Identifier("model_type"))

    # NOTE (mristin, 2023-07-12):
    # We use ``to_string`` naming to resemble the functions in standard library.
    return Stripped(
        f"""\
/**
 * Translate the enumeration literal \\p {model_type_arg} to text.
 *
 * \\param {model_type_arg} to be converted into text
 * \\return text representation of \\p {model_type_arg}
 * \\throw std::invalid_argument if \\p {model_type_arg} invalid
 */
std::string to_string(
{I}types::{enum_name} {model_type_arg}
);"""
    )


def _generate_model_type_to_string_implementation(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the implementation for translating a string to a model type."""
    enum_name = cpp_naming.enum_name(Identifier("Model_type"))

    case_blocks = []  # type: List[Stripped]
    for cls in symbol_table.concrete_classes:
        literal_name = cpp_naming.enum_literal_name(cls.name)
        literal_value = cpp_common.string_literal(
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
{IIII}static_cast<std::uint32_t>(
{IIIII}{model_type_arg}
{IIII})
{III})
{II})
{I});"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    # NOTE (mristin, 2023-07-12):
    # We use ``to_string`` naming to resemble the functions in standard library.
    return Stripped(
        f"""\
std::string to_string(
{I}types::{enum_name} {model_type_arg}
) {{
{I}switch ({model_type_arg}) {{
{II}{indent_but_first_line(case_blocks_joined, II)}
{I}}}
}}"""
    )


def _generate_enum_from_string_definition(
    enum: intermediate.Enumeration,
) -> List[Stripped]:
    """Generate the definition of translation of an enum from string."""
    enum_name = cpp_naming.enum_name(enum.name)
    from_string = cpp_naming.function_name(Identifier(f"{enum.name}_from_string"))
    must_from_string = cpp_naming.function_name(
        Identifier(f"must_{enum.name}_from_string")
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
common::optional<types::{enum_name}> {from_string}(
{I}const std::string& text
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
types::{enum_name} {must_from_string}(
{I}const std::string& text
);"""
        ),
    ]


def _generate_enum_from_string_implementation(
    enum: intermediate.Enumeration,
) -> List[Stripped]:
    """Generate the implementation of translation of an  enum from string."""
    blocks = []  # type: List[Stripped]

    # region Map

    enum_name = cpp_naming.enum_name(enum.name)

    items = []  # type: List[str]
    for literal in enum.literals:
        literal_name = cpp_naming.enum_literal_name(literal.name)
        literal_value = cpp_common.string_literal(literal.value)

        items.append(
            Stripped(
                f"""\
{{
{I}{literal_value},
{I}types::{enum_name}::{literal_name}
}}"""
            )
        )

    map_name = cpp_naming.constant_name(Identifier(f"{enum.name}_from_string_map"))

    items_joined = ",\n".join(items)

    blocks.append(
        Stripped(
            f"""\
const std::unordered_map<
{I}std::string,
{I}types::{enum_name}
> {map_name} = {{
{I}{indent_but_first_line(items_joined, I)}
}};"""
        )
    )

    # endregion

    # region From function

    from_string = cpp_naming.function_name(Identifier(f"{enum.name}_from_string"))

    blocks.append(
        Stripped(
            f"""\
common::optional<types::{enum_name}> {from_string}(
{I}const std::string& text
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

    must_from_string = cpp_naming.function_name(
        Identifier(f"must_{enum.name}_from_string")
    )

    blocks.append(
        Stripped(
            f"""\
types::{enum_name} {must_from_string}(
{I}const std::string& text
) {{
{I}const auto it = {map_name}.find(
{II}text
{I});
{I}if (it == {map_name}.end()) {{
{II}throw std::invalid_argument(
{III}common::Concat(
{IIII}"Unexpected {enum_name} literal: ",
{IIII}text
{III})
{II});
{I}}}
{I}return it->second;
}}"""
        )
    )

    # endregion

    return blocks


def _generate_enum_to_string_definition(enum: intermediate.Enumeration) -> Stripped:
    """Generate the definition for translating a string to an enum literal."""
    enum_name = cpp_naming.enum_name(enum.name)

    literal_arg = cpp_naming.argument_name(Identifier("literal"))

    # NOTE (mristin, 2023-07-12):
    # We use ``to_string`` naming to resemble the functions in standard library.
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
std::string to_string(
{I}types::{enum_name} {literal_arg}
);"""
    )


def _generate_enum_to_string_implementation(enum: intermediate.Enumeration) -> Stripped:
    """Generate the implementation for translating a string to an enum literal."""
    enum_name = cpp_naming.enum_name(enum.name)

    case_blocks = []  # type: List[Stripped]
    for literal in enum.literals:
        literal_name = cpp_naming.enum_literal_name(literal.name)
        literal_value = cpp_common.string_literal(literal.value)

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
{IIII}static_cast<std::uint32_t>(
{IIIII}{literal_arg}
{IIII})
{III})
{II})
{I});"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    # NOTE (mristin, 2023-07-12):
    # We use ``to_string`` naming to resemble the functions in standard library.
    return Stripped(
        f"""\
std::string to_string(
{I}types::{enum_name} {literal_arg}
) {{
{I}switch ({literal_arg}) {{
{II}{indent_but_first_line(case_blocks_joined, II)}
{I}}}
}}"""
    )


def _generate_base64_encode_definition() -> Stripped:
    """Generate the definition of the base64 encoding of bytes to a string."""
    function_name = cpp_naming.function_name(Identifier("base64_encode"))
    return Stripped(
        f"""\
/**
 * Encode the \\p bytes with base64 to a std::string.
 *
 * \\param bytes to be encoded
 * \\return base64-encoding of \\p bytes
 */
std::string {function_name}(
{I}const std::vector<std::uint8_t>& bytes
);"""
    )


def _generate_base64_encode_implementation() -> List[Stripped]:
    """Generate the implementation of the base64 encoding of bytes to a string."""
    char_base64_table = cpp_naming.constant_name(Identifier("char_base64_table"))
    char_base64_table_len = cpp_naming.constant_name(
        Identifier("char_base64_table_len")
    )

    function_name = cpp_naming.function_name(Identifier("base64_encode"))
    # noinspection SpellCheckingInspection
    return [
        Stripped(
            """\
// The following encoder has been adapted from Jouni Malinen <j@w1.fi> to work with
// std::string. The original source code is available at:
// https://web.mit.edu/freebsd/head/contrib/wpa/src/utils/base64.c
//
// See also the following StackOverflow question for a benchmark:
// https://stackoverflow.com/questions/342409/how-do-i-base64-encode-decode-in-c/41094722#41094722"""
        ),
        Stripped(
            f"""\
constexpr std::size_t {char_base64_table_len} = 65;
static const unsigned char {char_base64_table}[{char_base64_table_len}](
{I}"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
);"""
        ),
        Stripped(
            f"""\
std::string {function_name}(
{I}const std::vector<std::uint8_t>& bytes
) {{
{I}// See: https://cplusplus.com/reference/vector/vector/data/.
{I}// The data is guaranteed to be a continuous block in memory.
{I}const unsigned char* const src(
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

{I}std::string out_string;
{I}out_string.resize(olen);

{I}unsigned char* out(
{II}reinterpret_cast<unsigned char*>(
{III}&out_string[0]
{II})
{I});

{I}const unsigned char* const end = src + len;

{I}const unsigned char* in = src;
{I}unsigned char* pos = out;

{I}while (end - in >= 3) {{
{II}*pos++ = {char_base64_table}[in[0] >> 2];
{II}*pos++ = {char_base64_table}[((in[0] & 0x03) << 4) | (in[1] >> 4)];
{II}*pos++ = {char_base64_table}[((in[1] & 0x0f) << 2) | (in[2] >> 6)];
{II}*pos++ = {char_base64_table}[in[2] & 0x3f];
{II}in += 3;
{I}}}

{I}if (end - in) {{
{II}*pos++ = {char_base64_table}[in[0] >> 2];

{II}if (end - in == 1) {{
{III}*pos++ = {char_base64_table}[(in[0] & 0x03) << 4];
{III}*pos++ = '=';
{II}}} else {{
{III}*pos++ = {char_base64_table}[
{IIII}((in[0] & 0x03) << 4) | (in[1] >> 4)
{III}];
{III}*pos++ = {char_base64_table}[(in[1] & 0x0f) << 2];
{II}}}
{II}*pos++ = '=';
{I}}}

{I}return out_string;
}}"""
        ),
    ]


def _generate_base64_decode_definition() -> Stripped:
    """Generate the definition of the base64 decoding of a string to bytes."""
    # NOTE (mristin, 2023-07-12):
    # We decode intentionally from ``std::string``, and
    function_name = cpp_naming.function_name(Identifier("base64_decode"))
    return Stripped(
        f"""\
/**
 * Decode the \\p the text with base64 to bytes.
 *
 * \\remark \\parblock
 * We intentionally decode from std::string and *not* from std::wstring as
 * the de/serialization libraries currently work only with UTF-8 encoded strings.
 * \\endparblock
 *
 * \\param text to be decoded
 * \\return decoded bytes, or error message, if any.
 */
common::expected<
{I}std::vector<std::uint8_t>,
{I}std::string
> {function_name}(
{I}const std::string& text
);"""
    )


def _generate_base64_decode_implementation() -> List[Stripped]:
    """Generate the implementation of the base64 decoding of a string to bytes."""
    function_name = cpp_naming.function_name(Identifier("base64_decode"))
    base64_lookup = cpp_naming.constant_name(Identifier("base64_lookup"))

    char_base64_table = cpp_naming.constant_name(Identifier("char_base64_table"))
    char_base64_table_len = cpp_naming.constant_name(
        Identifier("char_base64_table_len")
    )

    construct_base64_lookup = cpp_naming.function_name(
        Identifier("construct_base64_lookup")
    )

    return [
        Stripped(
            """\
// The following decoder is vaguely based on:
// https://github.com/danguer/blog-examples/blob/master/js/base64-binary.js,
// https://github.com/niklasvh/base64-arraybuffer/blob/master/src/index.ts and
// https://github.com/beatgammit/base64-js/blob/master/index.js."""
        ),
        Stripped(
            f"""\
std::vector<std::uint8_t> {construct_base64_lookup}() {{
{I}std::vector<std::uint8_t> lookup(256, 255);
{I}for (std::uint8_t i = 0; i < {char_base64_table_len}; ++i) {{
{II}lookup.at({char_base64_table}[i]) = i;
{I}}}
{I}return lookup;
}}
const std::vector<std::uint8_t> {base64_lookup} = {construct_base64_lookup}();"""
        ),
        Stripped(
            f"""\
common::expected<
{I}std::vector<std::uint8_t>,
{I}std::string
> {function_name}(
{I}const std::string& text
) {{
{I}if (text.empty()) {{
{II}return std::vector<std::uint8_t>();
{I}}}

{I}const std::size_t len = text.size();
{I}std::size_t len_wo_pad = len;

{I}// NOTE (mristin):
{I}// Some implementations forget the padding, so we try to be robust and check
{I}// for the padding manually.
{I}std::size_t bytes_length = (len * 3) / 4;
{I}if (text[len - 1] == '=') {{
{II}bytes_length--;
{II}len_wo_pad--;

{II}if (text[len - 2] == '=') {{
{III}bytes_length--;
{III}len_wo_pad--;
{II}}}
{I}}}

{I}std::vector<std::uint8_t> bytes(bytes_length);

{I}const std::size_t base64_lookup_len = {base64_lookup}.size();

{I}std::size_t pointer = 0;

{I}for (std::size_t i = 0; i < len; i += 4) {{
{II}// NOTE (mristin):
{II}// Admittedly, this is very verbose code, but we want to be efficient, so we
{II}// opted for performance over readability here.

{II}const unsigned char code0 = text[i];
{II}if (code0 >= base64_lookup_len) {{
{III}std::string message = common::Concat(
{IIII}"Expected a valid character from base64-encoded string, "
{IIII}"but got at index ",
{IIII}std::to_string(i),
{IIII}": ",
{IIII}std::to_string(code0),
{IIII}" (code: ",
{IIII}std::to_string(static_cast<int>(code0)),
{IIII}")"
{III});

{III}return common::make_unexpected(message);
{II}}}
{II}const std::uint8_t encoded0 = {base64_lookup}[code0];
{II}if (encoded0 == 255) {{
{III}std::string message = common::Concat(
{IIII}"Expected a valid character from base64-encoded string, "
{IIII}"but got at index ",
{IIII}std::to_string(i),
{IIII}": ",
{IIII}std::to_string(code0),
{IIII}" (code: ",
{IIII}std::to_string(static_cast<int>(code0)),
{IIII}")"
{III});

{III}return common::make_unexpected(message);
{II}}}

{II}const unsigned char code1 = text[i + 1];
{II}if (code1 >= base64_lookup_len) {{
{III}std::string message = common::Concat(
{IIII}"Expected a valid character from base64-encoded string, "
{IIII}"but got at index ",
{IIII}std::to_string(i + 1),
{IIII}": ",
{IIII}std::to_string(code1),
{IIII}" (code: ",
{IIII}std::to_string(static_cast<int>(code1)),
{IIII}")"
{III});

{III}return common::make_unexpected(message);
{II}}}
{II}const std::uint8_t encoded1 = {base64_lookup}[code1];
{II}if (encoded1 == 255) {{
{III}std::string message = common::Concat(
{IIII}"Expected a valid character from base64-encoded string, "
{IIII}"but got at index ",
{IIII}std::to_string(i + 1),
{IIII}": ",
{IIII}std::to_string(code1),
{IIII}" (code: ",
{IIII}std::to_string(static_cast<int>(code1)),
{IIII}")"
{III});

{III}return common::make_unexpected(message);
{II}}}

{II}// We map padding to 65, which is the value of "A".
{II}const unsigned char code2 = i + 2 < len_wo_pad ? text[i + 2] : 65;
{II}if (code2 >= base64_lookup_len) {{
{III}std::string message = common::Concat(
{IIII}"Expected a valid character from base64-encoded string, "
{IIII}"but got at index ",
{IIII}std::to_string(i + 2),
{IIII}": ",
{IIII}std::to_string(code2),
{IIII}" (code: ",
{IIII}std::to_string(static_cast<int>(code2)),
{IIII}")"
{III});

{III}return common::make_unexpected(message);
{II}}}
{II}const std::uint8_t encoded2 = {base64_lookup}[code2];
{II}if (encoded2 == 255) {{
{III}std::string message = common::Concat(
{IIII}"Expected a valid character from base64-encoded string, "
{IIII}"but got at index ",
{IIII}std::to_string(i + 2),
{IIII}": ",
{IIII}std::to_string(code2),
{IIII}" (code: ",
{IIII}std::to_string(static_cast<int>(code2)),
{IIII}")"
{III});

{III}return common::make_unexpected(message);
{II}}}

{II}// We map padding to 65, which is the value of 'A'.
{II}const unsigned char code3 = i + 3 < len_wo_pad ? text[i + 3] : 65;
{II}if (code3 >= base64_lookup_len) {{
{III}std::string message = common::Concat(
{IIII}"Expected a valid character from base64-encoded string, "
{IIII}"but got at index ",
{IIII}std::to_string(i + 3),
{IIII}": ",
{IIII}std::to_string(code3),
{IIII}" (code: ",
{IIII}std::to_string(static_cast<int>(code3)),
{IIII}")"
{III});

{III}return common::make_unexpected(message);
{II}}}
{II}const std::uint8_t encoded3 = {base64_lookup}[code3];
{II}if (encoded3 == 255) {{
{III}std::string message = common::Concat(
{IIII}"Expected a valid character from base64-encoded string, "
{IIII}"but got at index ",
{IIII}std::to_string(i + 3),
{IIII}": ",
{IIII}std::to_string(code3),
{IIII}" (code: ",
{IIII}std::to_string(static_cast<int>(code3)),
{IIII}")"
{III});

{III}return common::make_unexpected(message);
{II}}}

{II}if (pointer >= bytes_length) {{
{III}break;
{II}}}
{II}bytes[pointer] = (encoded0 << 2) | (encoded1 >> 4);
{II}pointer++;

{II}if (pointer >= bytes_length) {{
{III}break;
{II}}}
{II}bytes[pointer] = ((encoded1 & 15) << 4) | (encoded2 >> 2);
{II}pointer++;

{II}if (pointer >= bytes_length) {{
{III}break;
{II}}}
{II}bytes[pointer] = ((encoded2 & 3) << 6) | (encoded3 & 63);
{II}pointer++;
{I}}}

{I}return bytes;
}}"""
        ),
    ]


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
    namespace = Stripped(f"{library_namespace}::stringification")

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
 * \\defgroup stringification Translate to strings, and, where applicable, from strings.
 * @{
 */
namespace stringification {"""
        ),
        *_generate_model_type_from_string_definition(),
        _generate_model_type_to_string_definition(),
    ]

    for enum in symbol_table.enumerations:
        blocks.extend(_generate_enum_from_string_definition(enum=enum))
        blocks.append(_generate_enum_to_string_definition(enum=enum))

    blocks.extend(
        [
            _generate_base64_encode_definition(),
            _generate_base64_decode_definition(),
            cpp_common.generate_namespace_closing(namespace),
            Stripped("/**@}*/"),
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
    namespace = Stripped(f"{library_namespace}::stringification")

    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            f"""\
#include "{include_prefix_path}/stringification.hpp"

#pragma warning(push, 0)
#include <unordered_map>
#pragma warning(pop)"""
        ),
        cpp_common.generate_namespace_opening(namespace),
        *_generate_model_type_from_string_implementation(symbol_table=symbol_table),
        _generate_model_type_to_string_implementation(symbol_table=symbol_table),
    ]  # type: List[Stripped]

    for enum in symbol_table.enumerations:
        blocks.extend(_generate_enum_from_string_implementation(enum=enum))
        blocks.append(_generate_enum_to_string_implementation(enum=enum))

    blocks.extend(
        [
            *_generate_base64_encode_implementation(),
            *_generate_base64_decode_implementation(),
            Stripped(
                """\
}  // namespace stringification
/**@}*/"""
            ),
            cpp_common.generate_namespace_closing(library_namespace),
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
