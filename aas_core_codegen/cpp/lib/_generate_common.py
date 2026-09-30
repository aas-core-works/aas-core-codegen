"""Generate code of common functionality."""

# pylint: disable=line-too-long

import io
from typing import Final, List, Sequence

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Identifier,
    Stripped,
    indent_but_first_line,
)
from aas_core_codegen.cpp import (
    common as cpp_common,
)
from aas_core_codegen.cpp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)
from aas_core_codegen.intermediate import uses as intermediate_uses


def _generate_concatenate_definitions_for_2_parts_and_above() -> List[Stripped]:
    """
    Generate the definition of ``concat`` functions.

    >>> print(_generate_concatenate_definitions_for_2_parts_and_above()[0])
    /**
     * Concatenate 2 strings.
     *
     * \\param part0 1st part of the concatenation
     * \\param part1 2nd part of the concatenation
     * \\return a concatenation of the 2 parts
     */
    std::string Concat(
      const std::string& part0,
      const std::string& part1
    );
    """
    concat_funcs = []  # type: List[Stripped]
    for string_type in ["std::string", "std::wstring"]:
        for count in range(2, 65):
            param_descriptions = []  # type: List[str]
            for i in range(0, count):
                ordinal: str

                ordinal_i = i + 1

                if ordinal_i % 10 == 1:
                    ordinal = f"{ordinal_i}st"
                elif ordinal_i % 10 == 2:
                    ordinal = f"{ordinal_i}nd"
                elif ordinal_i % 10 == 3:
                    ordinal = f"{ordinal_i}rd"
                else:
                    ordinal = f"{ordinal_i}th"

                param_descriptions.append(
                    f" * \\param part{i} {ordinal} part of the concatenation"
                )
            param_description_joined = "\n".join(param_descriptions)

            args_definition = ",\n".join(
                f"{I}const {string_type}& part{i}" for i in range(0, count)
            )

            concat_funcs.append(
                Stripped(
                    f"""\
/**
 * Concatenate {count} strings.
 *
{param_description_joined}
 * \\return a concatenation of the {count} parts
 */
{string_type} Concat(
{args_definition}
);"""
                )
            )

    return concat_funcs


def _generate_concatenate_implementations_for_2_parts_and_above() -> List[Stripped]:
    """
    Generate the implementation of ``concat`` functions.

    >>> print(_generate_concatenate_implementations_for_2_parts_and_above()[0])
    std::string Concat(
      const std::string& part0,
      const std::string& part1
    ) {
      size_t size = 0;
      size += part0.size();
      size += part1.size();
    <BLANKLINE>
      std::string result;
      result.reserve(size);
    <BLANKLINE>
      result.append(part0);
      result.append(part1);
    <BLANKLINE>
      return result;
    }
    """
    concat_funcs = []  # type: List[Stripped]
    for string_type in ["std::string", "std::wstring"]:
        for count in range(2, 65):
            args_definition = ",\n".join(
                f"{I}const {string_type}& part{i}" for i in range(0, count)
            )

            size_block = Stripped(
                "\n".join(f"size += part{i}.size();" for i in range(0, count))
            )

            append_block = Stripped(
                "\n".join(f"result.append(part{i});" for i in range(0, count))
            )

            concat_funcs.append(
                Stripped(
                    f"""\
{string_type} Concat(
{args_definition}
) {{
{I}size_t size = 0;
{I}{indent_but_first_line(size_block, I)}

{I}{string_type} result;
{I}result.reserve(size);

{I}{indent_but_first_line(append_block, I)}

{I}return result;
}}"""
                )
            )

    return concat_funcs


def _generate_string_helper_declarations(
    symbol_table: intermediate.SymbolTable,
) -> List[Stripped]:
    """
    Generate the declarations of the helpers for ``len``, slicing strings and ``find``.

    The helpers follow the Python implementation, since Python is the language of
    the meta-model specifications. Hence, the lengths and the positions count
    the characters (code points), while ``std::wstring`` counts the ``wchar_t``'s,
    which are UTF-16 code units on Windows, where a character beyond the Basic
    Multilingual Plane takes two of them (a surrogate pair). Moreover, the native
    ``std::wstring::substr`` throws on a start out of range, and neither ``substr``
    nor ``find`` count the negative positions from the end. We also accept
    the positions as ``int64_t``'s, since our integers are ``int64_t``'s in C++.

    We add ``LStrip`` only if the meta-model uses ``str.lstrip``.
    """
    result = [
        Stripped(
            """\
/**
 * Count the characters (code points) of \\p text.
 *
 * We follow the Python implementation of `len`, since Python is the language of
 * the meta-model specifications. Hence, a character beyond the Basic
 * Multilingual Plane counts as one, unlike in `text.size()` on the platforms
 * where `wchar_t` is a UTF-16 code unit, such as Windows.
 *
 * \\param text to be measured
 * \\return the number of characters
 */
size_t LenStr(const std::wstring& text);"""
        ),
        Stripped(
            f"""\
/**
 * Slice \\p text from \\p start up to \\p end, exclusive.
 *
 * We follow the Python implementation of slicing, since Python is the language
 * of the meta-model specifications. Hence, the positions count the characters
 * (code points), a negative position counts from the end, the positions out of
 * range are clamped to the string, and the slice is empty if \\p start is not
 * before \\p end.
 *
 * \\param text to be sliced
 * \\param start of the slice, inclusive
 * \\param end of the slice, exclusive
 * \\return the slice
 */
std::wstring SliceStr(
{I}const std::wstring& text,
{I}int64_t start,
{I}int64_t end
);"""
        ),
        Stripped(
            f"""\
/**
 * Slice \\p text from \\p start up to its end.
 *
 * See the other overload for the semantics.
 *
 * \\param text to be sliced
 * \\param start of the slice, inclusive
 * \\return the slice
 */
std::wstring SliceStr(
{I}const std::wstring& text,
{I}int64_t start
);"""
        ),
        Stripped(
            f"""\
/**
 * Find the first \\p sub in \\p text.
 *
 * See the other overload for the semantics.
 *
 * \\param text to be searched in
 * \\param sub to be searched for
 * \\return the position of \\p sub in \\p text, or -1 if not found
 */
int64_t FindStr(
{I}const std::wstring& text,
{I}const std::wstring& sub
);"""
        ),
        Stripped(
            f"""\
/**
 * Find the first \\p sub in \\p text from \\p start on.
 *
 * We follow the Python implementation of `str.find`, since Python is
 * the language of the meta-model specifications. Hence, the positions count
 * the characters (code points), a negative \\p start counts from the end, and
 * a \\p start beyond the end of \\p text gives -1.
 *
 * \\param text to be searched in
 * \\param sub to be searched for
 * \\param start of the search
 * \\return the position of \\p sub in \\p text, or -1 if not found
 */
int64_t FindStr(
{I}const std::wstring& text,
{I}const std::wstring& sub,
{I}int64_t start
);"""
        ),
    ]  # type: List[Stripped]

    if intermediate_uses.lstrip_call(symbol_table):
        result.append(
            Stripped(
                f"""\
/**
 * Strip the longest prefix of \\p text consisting of the \\p chars.
 *
 * We follow the Python implementation of `str.lstrip`, since Python is
 * the language of the meta-model specifications. Hence, we strip
 * the characters (code points), and never a half of a surrogate pair on
 * the platforms where `wchar_t` is a UTF-16 code unit, such as Windows.
 *
 * \\param text to be stripped
 * \\param chars to be stripped from the start of \\p text
 * \\return \\p text without the stripped prefix
 */
std::wstring LStrip(
{I}const std::wstring& text,
{I}const std::wstring& chars
);"""
            )
        )

    return result


def _generate_string_helper_definitions(
    symbol_table: intermediate.SymbolTable,
) -> List[Stripped]:
    """
    Generate the definitions of the helpers for ``len``, slicing strings and ``find``.

    We add ``LStrip`` only if the meta-model uses ``str.lstrip``.
    """
    # NOTE (mristin):
    # We count a lone surrogate as a character of its own, as Python does. We do
    # not check whether ``find`` matches in the middle of a surrogate pair, as
    # that could only happen if the searched text started or ended with a lone
    # surrogate.
    result = [
        Stripped(
            f"""\
namespace {{

// NOTE (mristin):
// The type wchar_t is a UTF-16 code unit on Windows, where a character beyond
// the Basic Multilingual Plane takes two of them (a surrogate pair). On the other
// platforms, wchar_t is a UTF-32 code unit, so that each character takes exactly
// one wchar_t.
#if WCHAR_MAX <= 0xFFFF
/**
 * Check whether a surrogate pair starts at \\p offset in \\p text.
 */
bool IsSurrogatePairAt(const std::wstring& text, size_t offset) {{
{I}return (
{II}offset + 1 < text.size()
{II}&& text[offset] >= 0xD800
{II}&& text[offset] <= 0xDBFF
{II}&& text[offset + 1] >= 0xDC00
{II}&& text[offset + 1] <= 0xDFFF
{I});
}}

/**
 * Count the characters of \\p text between \\p start_offset and
 * \\p end_offset, both in wchar_t's.
 */
size_t CountCharacters(
{I}const std::wstring& text,
{I}size_t start_offset,
{I}size_t end_offset
) {{
{I}size_t count = 0;
{I}size_t offset = start_offset;
{I}while (offset < end_offset) {{
{II}offset += IsSurrogatePairAt(text, offset) ? 2 : 1;
{II}++count;
{I}}}

{I}return count;
}}

/**
 * Compute the offset in wchar_t's of the character at \\p position
 * in \\p text.
 */
size_t OffsetOf(const std::wstring& text, size_t position) {{
{I}size_t offset = 0;
{I}for (size_t i = 0; i < position; ++i) {{
{II}offset += IsSurrogatePairAt(text, offset) ? 2 : 1;
{I}}}

{I}return offset;
}}
#else
/**
 * Count the characters of a text between \\p start_offset and
 * \\p end_offset, both in wchar_t's.
 */
size_t CountCharacters(
{I}const std::wstring&,
{I}size_t start_offset,
{I}size_t end_offset
) {{
{I}return end_offset - start_offset;
}}

/**
 * Compute the offset in wchar_t's of the character at \\p position
 * in a text.
 */
size_t OffsetOf(const std::wstring&, size_t position) {{
{I}return position;
}}
#endif

/**
 * Resolve \\p position in a string of \\p length as Python does in slicing.
 *
 * A negative position counts from the end, and the positions out of range are
 * clamped to the string.
 *
 * \\param position to be resolved
 * \\param length of the string
 * \\return the resolved position within `[0, length]`
 */
size_t ResolvePosition(int64_t position, size_t length) {{
{I}const int64_t signed_length = static_cast<int64_t>(length);

{I}if (position < 0) {{
{II}const int64_t resolved = position + signed_length;
{II}return resolved < 0 ? 0 : static_cast<size_t>(resolved);
{I}}}

{I}return position > signed_length ? length : static_cast<size_t>(position);
}}

}}  // namespace"""
        ),
        Stripped(
            f"""\
size_t LenStr(const std::wstring& text) {{
{I}return CountCharacters(text, 0, text.size());
}}"""
        ),
        Stripped(
            f"""\
std::wstring SliceStr(
{I}const std::wstring& text,
{I}int64_t start,
{I}int64_t end
) {{
{I}const size_t length = LenStr(text);
{I}const size_t the_start = ResolvePosition(start, length);
{I}const size_t the_end = ResolvePosition(end, length);

{I}if (the_start >= the_end) {{
{II}return L"";
{I}}}

{I}const size_t start_offset = OffsetOf(text, the_start);
{I}const size_t end_offset = OffsetOf(text, the_end);
{I}return text.substr(start_offset, end_offset - start_offset);
}}"""
        ),
        Stripped(
            f"""\
std::wstring SliceStr(
{I}const std::wstring& text,
{I}int64_t start
) {{
{I}return text.substr(
{II}OffsetOf(text, ResolvePosition(start, LenStr(text)))
{I});
}}"""
        ),
        Stripped(
            f"""\
int64_t FindStr(
{I}const std::wstring& text,
{I}const std::wstring& sub
) {{
{I}return FindStr(text, sub, 0);
}}"""
        ),
        Stripped(
            f"""\
int64_t FindStr(
{I}const std::wstring& text,
{I}const std::wstring& sub,
{I}int64_t start
) {{
{I}const int64_t length = static_cast<int64_t>(LenStr(text));

{I}int64_t the_start = start;
{I}if (the_start < 0) {{
{II}the_start += length;
{II}if (the_start < 0) {{
{III}the_start = 0;
{II}}}
{I}}}

{I}if (the_start > length) {{
{II}return -1;
{I}}}

{I}const size_t start_offset = OffsetOf(text, static_cast<size_t>(the_start));
{I}const size_t offset = text.find(sub, start_offset);
{I}if (offset == std::wstring::npos) {{
{II}return -1;
{I}}}

{I}return the_start + static_cast<int64_t>(
{II}CountCharacters(text, start_offset, offset)
{I});
}}"""
        ),
    ]  # type: List[Stripped]

    if intermediate_uses.lstrip_call(symbol_table):
        result.extend(
            [
                Stripped(
                    f"""\
namespace {{

#if WCHAR_MAX <= 0xFFFF
/**
 * Compute the size in wchar_t's of the character at \\p offset in \\p text.
 */
size_t CharacterSizeAt(const std::wstring& text, size_t offset) {{
{I}return IsSurrogatePairAt(text, offset) ? 2 : 1;
}}
#else
/**
 * Compute the size in wchar_t's of a character in a text.
 */
size_t CharacterSizeAt(const std::wstring&, size_t) {{
{I}return 1;
}}
#endif

}}  // namespace"""
                ),
                Stripped(
                    f"""\
std::wstring LStrip(
{I}const std::wstring& text,
{I}const std::wstring& chars
) {{
{I}size_t offset = 0;
{I}while (offset < text.size()) {{
{II}const size_t size = CharacterSizeAt(text, offset);

{II}// NOTE (mristin):
{II}// We compare the whole characters so that we never strip a half of
{II}// a surrogate pair.
{II}bool stripped = false;
{II}size_t chars_offset = 0;
{II}while (chars_offset < chars.size()) {{
{III}const size_t chars_size = CharacterSizeAt(chars, chars_offset);
{III}if (
{IIII}chars_size == size
{IIII}&& chars.compare(chars_offset, chars_size, text, offset, size) == 0
{III}) {{
{IIII}stripped = true;
{IIII}break;
{III}}}

{III}chars_offset += chars_size;
{II}}}

{II}if (!stripped) {{
{III}break;
{II}}}

{II}offset += size;
{I}}}

{I}return text.substr(offset);
}}"""
                ),
            ]
        )

    return result


# NOTE (mristin):
# We deliberately do not transpile the modulo to the native C++ operator ``%`` for
# the signed operands. C++ truncates the division towards zero so that its remainder
# takes the sign of the dividend (``-7 % 3 == -1``). The meta-model is written in
# Python where the division is floored so that the remainder takes the sign of
# the divisor (``-7 % 3 == 2``). The two only coincide when the operands have
# the same sign, but the invariants must behave the same in all the SDKs for all
# the inputs. Hence, we transpile the modulo to the helper ``FloorMod`` below.
#
# The helper lives in the common module so that both the verification and
# the methods of the types can use it. It is public so that the clients can rely
# on it, and so that we can unit-test it.

#: Name of the helper function to compute the floored remainder
FLOOR_MOD_NAME: Final[Identifier] = Identifier("FloorMod")

#: Declaration of the helper to compute the remainder of the floored division as in
#: Python, to be put in the header
FLOOR_MOD_DECLARATION = Stripped(
    """\
/**
 * \\brief Compute the remainder of the floored division of \\p dividend
 * by \\p divisor.
 *
 * The remainder takes the sign of the divisor, as the modulo in Python,
 * in which the meta-model is written.
 *
 * We deliberately do not use the native operator <code>%</code> which truncates
 * the division towards zero so that its remainder takes the sign of the dividend.
 * For example, <code>-7 % 3 == -1</code> in C++, while <code>-7 % 3 == 2</code>
 * in Python. The two only coincide when the operands have the same sign, but
 * the invariants must behave the same in all the SDKs for all the inputs.
 *
 * The \\p divisor must not be zero.
 *
 * \\param dividend to be divided
 * \\param divisor to divide with, must not be zero
 * \\return remainder of the floored division, with the sign of \\p divisor
 */
int64_t FloorMod(int64_t dividend, int64_t divisor);"""
)

#: Definition of the helper to compute the remainder of the floored division as in
#: Python, to be put in the implementation
FLOOR_MOD_DEFINITION = Stripped(
    f"""\
int64_t FloorMod(int64_t dividend, int64_t divisor) {{
{I}// NOTE: The native INT64_MIN % -1 is undefined behavior in C++ as
{I}// the corresponding division overflows, while every number is divisible
{I}// by -1 without a remainder.
{I}if (divisor == -1) {{
{II}return 0;
{I}}}

{I}// NOTE: We can not use the native remainder directly as C++ truncates
{I}// the division towards zero so that the remainder takes the sign of
{I}// the dividend. We correct it to take the sign of the divisor as in Python.
{I}int64_t remainder = dividend % divisor;
{I}if (remainder != 0 && ((remainder < 0) != (divisor < 0))) {{
{II}remainder += divisor;
{I}}}

{I}return remainder;
}}"""
)


# NOTE (mristin):
# We deliberately do not transpile the built-in ``int`` to the native ``std::stoll``
# as it skips the leading white space, ignores the trailing characters, and depends
# on the locale. Moreover, it would parse the integers beyond the safe range, which
# TypeScript can not represent, so that the SDKs would behave differently. Hence, we
# transpile ``int`` to the helper ``ParseSafeInt`` below.
#
# The helper lives in the common module so that both the verification and
# the methods of the types can use it. It is public so that the clients can rely
# on it, and so that we can unit-test it.

#: Name of the helper function to parse the safe integers
PARSE_SAFE_INT_NAME: Final[Identifier] = Identifier("ParseSafeInt")

#: Declaration of the helper to parse a safe integer, to be put in the header
PARSE_SAFE_INT_DECLARATION = Stripped(
    """\
/**
 * \\brief Parse \\p text as a safe integer.
 *
 * The meta-model calls <code>int</code> on strings, and this is its
 * transpilation. We accept only an optional sign followed by the ASCII digits,
 * and only the safe integers, <em>i.e.</em>, the integers within
 * <code>-(2^53 - 1)</code> and <code>2^53 - 1</code>, which a double-precision
 * floating-point number represents exactly. This way, all the SDKs behave
 * the same.
 *
 * \\param text to be parsed
 * \\return parsed integer
 * \\throw std::invalid_argument if \\p text is not a safe integer
 */
int64_t ParseSafeInt(const std::wstring& text);"""
)

#: Definition of the helper to parse a safe integer, to be put in
#: the implementation
PARSE_SAFE_INT_DEFINITION = Stripped(
    f"""\
int64_t ParseSafeInt(const std::wstring& text) {{
{I}// NOTE: This is 2^53 - 1.
{I}const int64_t kMaxSafeInteger = 9007199254740991LL;

{I}size_t offset = 0;
{I}bool negative = false;
{I}if (!text.empty() && (text[0] == L'-' || text[0] == L'+')) {{
{II}negative = text[0] == L'-';
{II}offset = 1;
{I}}}

{I}if (offset == text.size()) {{
{II}throw std::invalid_argument(
{III}"Expected an optional sign followed by the ASCII digits, but got: "
{III}+ WstringToUtf8(text)
{II});
{I}}}

{I}int64_t value = 0;
{I}for (size_t i = offset; i < text.size(); ++i) {{
{II}const wchar_t character = text[i];
{II}if (character < L'0' || character > L'9') {{
{III}throw std::invalid_argument(
{IIII}"Expected an optional sign followed by the ASCII digits, but got: "
{IIII}+ WstringToUtf8(text)
{III});
{II}}}

{II}// NOTE: The value never overflows as we check it after each digit, and
{II}// ten times the largest safe integer fits into int64_t.
{II}value = value * 10 + static_cast<int64_t>(character - L'0');
{II}if (value > kMaxSafeInteger) {{
{III}throw std::invalid_argument(
{IIII}"Expected a safe integer, but got a text out of its range: "
{IIII}+ WstringToUtf8(text)
{III});
{II}}}
{I}}}

{I}return negative ? -value : value;
}}"""
)


#: Define the operations on sets which give a new set, as in Python
_SET_OPERATIONS_DEFINITIONS: Final[Sequence[Stripped]] = [
    Stripped(
        f"""\
/**
 * \\brief Give a new set of the items which are both in \\p that and
 * in \\p other.
 *
 * \\param that set to be intersected
 * \\param other set to intersect with
 * \\return new set with the common items
 */
template<typename SetT>
SetT Intersection(
{I}const SetT& that,
{I}const SetT& other
) {{
{I}SetT result;
{I}for (const auto& item : that) {{
{II}if (other.find(item) != other.end()) {{
{III}result.insert(item);
{II}}}
{I}}}
{I}return result;
}}"""
    ),
    Stripped(
        f"""\
/**
 * \\brief Give a new set of the items which are in \\p that, but not
 * in \\p other.
 *
 * \\param that set to be subtracted from
 * \\param other set of the items to be left out
 * \\return new set with the remaining items
 */
template<typename SetT>
SetT Difference(
{I}const SetT& that,
{I}const SetT& other
) {{
{I}SetT result;
{I}for (const auto& item : that) {{
{II}if (other.find(item) == other.end()) {{
{III}result.insert(item);
{II}}}
{I}}}
{I}return result;
}}"""
    ),
]


#: Declare the comparison of the strings by code points, by which we sort
#: the items of the set properties
_LESS_BY_CODE_POINTS_DECLARATION: Final[Stripped] = Stripped(
    f"""\
/**
 * \\brief Check whether \\p that text comes before \\p other text,
 * comparing them code point by code point.
 *
 * The comparison of std::wstring compares the code units. Where wchar_t has
 * 16 bits, as on Windows, the text is encoded in UTF-16, and the code units put
 * the characters above U+FFFF, encoded as surrogate pairs, before
 * the characters from U+E000 to U+FFFF. Hence we decode the code points and
 * compare them instead, in the same way on all the platforms.
 *
 * We sort the items of the sets by the code points in the serialization so that
 * all the SDKs write the same order.
 *
 * \\param that text to be compared
 * \\param other text to compare against
 * \\return `true` if \\p that comes before \\p other
 */
bool LessByCodePoints(
{I}const std::wstring& that,
{I}const std::wstring& other
);"""
)

#: Define the comparison of the strings by code points, by which we sort
#: the items of the set properties
_LESS_BY_CODE_POINTS_DEFINITION: Final[Stripped] = Stripped(
    f"""\
namespace {{

/**
 * Decode the code point at \\p offset in \\p text, and move \\p offset
 * past it.
 *
 * A high surrogate followed by a low surrogate is decoded as a single code
 * point. Any other code unit, including a lone surrogate, is taken as
 * the code point itself. Where wchar_t has 32 bits, as on Linux, a well-formed
 * text contains no surrogates, so that each code unit is a code point.
 */
std::uint32_t DecodeCodePoint(const std::wstring& text, size_t& offset) {{
{I}const std::uint32_t unit = static_cast<std::uint32_t>(text[offset]);
{I}++offset;

{I}if (
{II}unit >= 0xD800
{II}&& unit <= 0xDBFF
{II}&& offset < text.size()
{I}) {{
{II}const std::uint32_t next = static_cast<std::uint32_t>(text[offset]);
{II}if (next >= 0xDC00 && next <= 0xDFFF) {{
{III}++offset;
{III}return 0x10000 + ((unit - 0xD800) << 10) + (next - 0xDC00);
{II}}}
{I}}}

{I}return unit;
}}

}}  // namespace

bool LessByCodePoints(
{I}const std::wstring& that,
{I}const std::wstring& other
) {{
{I}size_t that_offset = 0;
{I}size_t other_offset = 0;

{I}while (that_offset < that.size() && other_offset < other.size()) {{
{II}const std::uint32_t that_code_point = DecodeCodePoint(that, that_offset);
{II}const std::uint32_t other_code_point = DecodeCodePoint(other, other_offset);

{II}if (that_code_point != other_code_point) {{
{III}return that_code_point < other_code_point;
{II}}}
{I}}}

{I}return other_offset < other.size();
}}"""
)

#: Define the hasher of the enumeration literals in the sets, as C++11 does not
#: specialize ``std::hash`` for the enumerations, which C++14 does
_ENUM_HASH_DEFINITION: Final[Stripped] = Stripped(
    f"""\
/**
 * \\brief Hash an enumeration literal by its underlying value.
 *
 * C++11 does not specialize std::hash for the enumerations, while C++14 does.
 * We use this hasher for all the sets of enumeration literals so that
 * the SDK stays C++11-compatible.
 */
struct EnumHash {{
{I}template<typename T>
{I}std::size_t operator()(T that) const {{
{II}return static_cast<std::size_t>(that);
{I}}}
}};"""
)


#: Define the sorting of the items of a set, which we need to serialize and
#: verify the set properties in the same order in all the SDKs
_SORTED_POINTERS_DEFINITION: Final[Stripped] = Stripped(
    f"""\
/**
 * \\brief Sort the pointers to the items of \\p set by \\p less.
 *
 * We sort the pointers instead of the items so that we copy no items.
 *
 * \\param set whose items are to be sorted
 * \\param less comparing two items
 * \\return pointers to the items, sorted
 */
template<typename SetT, typename LessT>
std::vector<const typename SetT::value_type*> SortedPointers(
{I}const SetT& set,
{I}LessT less
) {{
{I}typedef typename SetT::value_type T;

{I}std::vector<const T*> result;
{I}result.reserve(set.size());

{I}for (const T& item : set) {{
{II}result.push_back(&item);
{I}}}

{I}std::sort(
{II}result.begin(),
{II}result.end(),
{II}[&less](const T* that, const T* other) {{
{III}return less(*that, *other);
{II}}}
{I});

{I}return result;
}}"""
)


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
    """Generate header of common functionality."""
    namespace = Stripped(f"{library_namespace}")

    include_guard_var = cpp_common.include_guard_var(namespace)

    make_uniques = [
        Stripped(
            f"""\
template<typename T>
std::unique_ptr<T> make_unique() {{
{I}return std::unique_ptr<T>(
{II}new T()
{I});
}}"""
        )
    ]  # type: List[Stripped]
    for i in range(1, 16):
        typenames_joined = ",\n".join(
            ["typename T"] + [f"typename A{j + 1}" for j in range(i)]
        )

        args_joined = ",\n".join(f"A{j + 1}&& a{j + 1}" for j in range(i))

        forward_args_joined = ",\n".join(
            f"std::forward<A{j + 1}>(a{j + 1})" for j in range(i)
        )

        make_uniques.append(
            Stripped(
                f"""\
template<
{I}{indent_but_first_line(typenames_joined, I)}
>
std::unique_ptr<T> make_unique(
{I}{indent_but_first_line(args_joined, I)}
) {{
{I}return std::unique_ptr<T>(
{II}new T(
{III}{indent_but_first_line(forward_args_joined, III)}
{II})
{I});
}}"""
            )
        )

    make_uniques_joined = "\n\n".join(make_uniques)

    has_set_properties = intermediate_uses.set_properties(symbol_table)

    vector_include = "#include <vector>\n" if has_set_properties else ""

    blocks = [
        Stripped(
            f"""\
#ifndef {include_guard_var}
#define {include_guard_var}"""
        ),
        cpp_common.WARNING,
        Stripped(
            f"""\
#pragma warning(push, 0)
#include <algorithm>
#include <functional>
#include <memory>
#include <sstream>
#include <string>
#include <tuple>
#include <utility>
{vector_include}\
#pragma warning(pop)

// NOTE (mristin):
// See: https://stackoverflow.com/questions/2324658/how-to-determine-the-version-of-the-c-standard-used-by-the-compiler
#if ((defined(_MSVC_LANG) && _MSVC_LANG >= 201703L) || __cplusplus >= 201703L)
// NOTE (mristin):
// Standard library provides std::optional in C++17 and above.
#pragma warning(push, 0)
#include <optional>
#pragma warning(pop)
#else
// NOTE (mristin):
// We rely on https://github.com/TartanLlama/optional for optional structure.
#pragma warning(push, 0)
#include <tl/optional.hpp>
#pragma warning(pop)
#endif

// NOTE (mristin):
// We check for the version above C++20 as there is no C++23 literal yet, and
// std::expected is available only in C++23.
// See: https://stackoverflow.com/questions/2324658/how-to-determine-the-version-of-the-c-standard-used-by-the-compiler
// and: http://eel.is/c++draft/cpp.predefined#1.1
#if ((defined(_MSVC_LANG) && _MSVC_LANG > 202002L) || __cplusplus > 202002L)
// Standard library provides std::expected in C++23 and above.
#pragma warning(push, 0)
#include <expected>
#pragma warning(pop)
#else
// NOTE (mristin):
// We rely on https://github.com/TartanLlama/expected for expected structure.
#pragma warning(push, 0)
#include <tl/expected.hpp>
#pragma warning(pop)
#endif"""
        ),
    ]  # type: List[Stripped]

    # NOTE (mristin):
    # The string helpers take the positions as ``int64_t``'s, and need
    # ``WCHAR_MAX`` to tell whether ``wchar_t`` is a UTF-16 code unit. Hence, we
    # include these headers only for a meta-model which might take ``len`` of
    # strings, slice them, or call ``find`` or ``lstrip`` on them.
    #
    # The helpers ``FloorMod`` and ``ParseSafeInt`` return ``int64_t``'s as well.
    uses_string_helpers = intermediate_uses.len_slicing_or_find(
        symbol_table
    ) or intermediate_uses.lstrip_call(symbol_table)

    extra_std_includes = []  # type: List[str]
    if (
        uses_string_helpers
        or intermediate_uses.modulo(symbol_table)
        or intermediate_uses.int_call(symbol_table)
    ):
        extra_std_includes.append("#include <cstdint>")

    if uses_string_helpers:
        extra_std_includes.append("#include <cwchar>")

    if len(extra_std_includes) > 0:
        extra_std_includes_joined = "\n".join(extra_std_includes)
        blocks.append(
            Stripped(
                f"""\
#pragma warning(push, 0)
{extra_std_includes_joined}
#pragma warning(pop)"""
            )
        )

    # NOTE (mristin):
    # Only the named unions need a variant, so we do not burden the users of
    # the other meta-models with an additional dependency in C++11 and C++14.
    uses_variant = len(symbol_table.named_unions) > 0

    if uses_variant:
        blocks.append(
            Stripped(
                """\
// NOTE (mristin):
// See: https://stackoverflow.com/questions/2324658/how-to-determine-the-version-of-the-c-standard-used-by-the-compiler
#if ((defined(_MSVC_LANG) && _MSVC_LANG >= 201703L) || __cplusplus >= 201703L)
// NOTE (mristin):
// Standard library provides std::variant in C++17 and above.
#pragma warning(push, 0)
#include <variant>
#pragma warning(pop)
#else
// NOTE (mristin):
// We rely on https://github.com/mpark/variant for variant structure.
#pragma warning(push, 0)
#include <mpark/variant.hpp>
#pragma warning(pop)
#endif"""
            )
        )

    variant_aliases = (
        [
            Stripped(
                """\
// Please keep in sync with the preprocessing directives above in the include block.
#if ((defined(_MSVC_LANG) && _MSVC_LANG >= 201703L) || __cplusplus >= 201703L)
using std::variant;
using std::get;
using std::in_place_index_t;
#else
using mpark::variant;
using mpark::get;
using mpark::in_place_index_t;
#endif"""
            )
        ]
        if uses_variant
        else []
    )  # type: List[Stripped]

    blocks.extend(
        [
            cpp_common.generate_namespace_opening(library_namespace),
            Stripped(
                f"""\
/**
 * \\defgroup common Common functionality used throughout the library
 * @{{
 */
namespace {cpp_common.COMMON_NAMESPACE} {{"""
            ),
            Stripped(
                """\
// Please keep in sync with the preprocessing directives above in the include block.
#if ((defined(_MSVC_LANG) && _MSVC_LANG >= 201703L) || __cplusplus >= 201703L)
// Standard library provides std::optional in C++17 and above.
using std::optional;
using std::nullopt;
using std::make_optional;
#else
using tl::optional;
using tl::nullopt;
using tl::make_optional;
#endif"""
            ),
            Stripped(
                """\
// Please keep in sync with the preprocessing directives above in the include block.
#if ((defined(_MSVC_LANG) && _MSVC_LANG > 202002L) || __cplusplus > 202002L)
using std::expected;
using std::unexpected;
using std::make_unexpected;
#else
using tl::expected;
using tl::unexpected;
using tl::make_unexpected;
#endif"""
            ),
            *variant_aliases,
            Stripped(
                f"""\
// Please keep in sync with the preprocessing directives above in the include block.
// Standard library provides std::make_unique in C++14 and above.
#if ((defined(_MSVC_LANG) && _MSVC_LANG >= 201402L) || __cplusplus >= 201402L)
using std::make_unique;
#else
// Inspired by:
// https://stackoverflow.com/questions/12547983/is-there-a-way-to-write-make-unique-in-vs2012
{make_uniques_joined}
#endif"""
            ),
            *_generate_concatenate_definitions_for_2_parts_and_above(),
            Stripped(
                f"""\
/**
 * Check if all the elements satisfy the \\p condition.
 *
 * \\param condition returning a boolean to be checked for each element
 * \\param container to be iterated through
 * \\return `true` if all the elements of \\p container satisfy the \\p condition
 */
template<typename ContainerT, typename FunctorT>
bool All(
{I}FunctorT condition,
{I}const ContainerT& container
) {{
{I}for (const auto& item : container ) {{
{II}if (!condition(item)) {{
{III}return false;
{II}}}
{I}}}
{I}return true;
}}"""
            ),
            Stripped(
                f"""\
/**
 * Check if any of the elements satisfy the \\p condition.
 *
 * \\param condition returning a boolean to be checked for each element
 * \\param container to be iterated through
 * \\return `true` if any of the elements of \\p container satisfy the \\p condition
 */
template<typename ContainerT, typename FunctorT>
bool Some(
{I}FunctorT condition,
{I}const ContainerT& container
) {{
{I}for (const auto& item : container ) {{
{II}if (condition(item)) {{
{III}return true;
{II}}}
{I}}}
{I}return false;
}}"""
            ),
            Stripped(
                f"""\
/**
 * Check if all the numbers in the range `[start, end)` satisfy the \\p condition.
 *
 * The `IntegerT` is either `size_t` for the lengths, or `int64_t` for
 * the integers, and needs to be given explicitly.
 *
 * \\param condition returning a boolean to be checked for each number
 * \\param start of the range
 * \\param end of the range
 * \\return \\parblock
 * `true` if all the numbers between \\p start and \\p end (excluded)
 * satisfy the \\p condition
 * \\endparblock
 */
template<typename IntegerT, typename FunctorT>
bool AllRange(
{I}FunctorT condition,
{I}IntegerT start,
{I}IntegerT end
) {{
{I}for (IntegerT i = start; i < end; ++i) {{
{II}if (!condition(i)) {{
{III}return false;
{II}}}
{I}}}
{I}return true;
}}"""
            ),
            Stripped(
                f"""\
/**
 * Check if any number in the range `[start, end)` satisfy the \\p condition.
 *
 * The `IntegerT` is either `size_t` for the lengths, or `int64_t` for
 * the integers, and needs to be given explicitly.
 *
 * \\param condition returning a boolean to be checked for each number
 * \\param start of the range
 * \\param end of the range
 * \\return \\parblock
 * `true` if any number between \\p start and
 * \\p end (excluded) satisfy the \\p condition
 * \\endparblock
 */
template<typename IntegerT, typename FunctorT>
bool SomeRange(
{I}FunctorT condition,
{I}IntegerT start,
{I}IntegerT end
) {{
{I}for (IntegerT i = start; i < end; ++i) {{
{II}if (condition(i)) {{
{III}return true;
{II}}}
{I}}}
{I}return false;
}}"""
            ),
            Stripped(
                f"""\
/**
 * Check if the \\p container contains the \\p value.
 *
 * \\param container to be searched through
 * \\param value to be search for
 * \\return `true` if \\p value is in the \\p container
 */
template<typename ContainerT, typename ValueT>
bool Contains(
{I}const ContainerT& container,
{I}const ValueT& value
) {{
{I}const auto container_begin = std::begin(container);
{I}const auto container_end = std::end(container);
{I}return std::find(
{II}container_begin,
{II}container_end,
{II}value
{I}) != container_end;
}}"""
            ),
            Stripped(
                """\
/**
 * Convert platform-independent the wide string to a UTF-8 string.
 *
 * \\param text to be converted
 * \\return UTF-8 encoded \\p text
 */
std::string WstringToUtf8(const std::wstring& text);"""
            ),
            Stripped(
                f"""\
/**
 * Convert platform-independent the UTF-8 encoded string to a wide string.
 *
 * \\param utf8_text UTF-8 encoded text to be converted
 * \\param utf8_text_size size of the text to be converted. If std::string::npos,
 * the \\p utf8_text is assumed to be null-terminated and the size is determined
 * using `strlen`.
 * \\return the wide-string representation
 */
std::wstring Utf8ToWstring(
{I}const char* utf8_text,
{I}size_t utf8_text_size = std::string::npos
);"""
            ),
            Stripped(
                """\
/**
 * Convert platform-independent the UTF-8 encoded string to a wide string.
 *
 * \\param utf8_text UTF-8 encoded text to be converted
 * \\return wide string
 */
std::wstring Utf8ToWstring(const std::string& utf8_text);"""
            ),
            Stripped(
                """\
/**
 * Count the items of a tuple.
 *
 * \\return the number of items
 */
template<typename... T>
size_t LenTuple(const std::tuple<T...>&) {
  return sizeof...(T);
}"""
            ),
            *(
                _generate_string_helper_declarations(symbol_table)
                if uses_string_helpers
                else []
            ),
            *(
                [FLOOR_MOD_DECLARATION]
                if intermediate_uses.modulo(symbol_table)
                else []
            ),
            *(
                [PARSE_SAFE_INT_DECLARATION]
                if intermediate_uses.int_call(symbol_table)
                else []
            ),
            *(
                _SET_OPERATIONS_DEFINITIONS
                if intermediate_uses.set_operations(symbol_table)
                else []
            ),
            *(
                [_LESS_BY_CODE_POINTS_DECLARATION]
                if intermediate_uses.sets_of_strings_in_properties(symbol_table)
                else []
            ),
            *([_SORTED_POINTERS_DEFINITION] if has_set_properties else []),
            *(
                [_ENUM_HASH_DEFINITION]
                if intermediate_uses.sets_of_enumeration_literals(symbol_table)
                else []
            ),
            Stripped(
                f"""\
}}  // namespace {cpp_common.COMMON_NAMESPACE}
/**@}}*/"""
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
    """Generate implementation of common functionality."""
    namespace = Stripped(f"{library_namespace}::{cpp_common.COMMON_NAMESPACE}")

    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    # NOTE (mristin):
    # ``ParseSafeInt`` throws ``std::invalid_argument``.
    std_includes = ["#include <algorithm>"]
    if intermediate_uses.int_call(symbol_table):
        std_includes.append("#include <stdexcept>")

    # NOTE (mristin):
    # ``LessByCodePoints`` needs ``std::uint32_t``.
    if intermediate_uses.sets_of_strings_in_properties(symbol_table):
        std_includes.append("#include <cstdint>")

    std_includes_joined = "\n".join(std_includes)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            f'''\
#include "{include_prefix_path}/common.hpp"'''
        ),
        Stripped(
            f"""\
#pragma warning(push, 0)
{std_includes_joined}
#pragma warning(pop)

// NOTE (mristin):
// We use MultiByteToWideChar and WideCharToMulitByte from <windows.h> on Windows
// as std::codecvt is not robust enough on Windows, and produces invalid UTF-16
// sequences as std::wstring. See:
// https://stackoverflow.com/questions/2573834/c-convert-string-or-char-to-wstring-or-wchar-t,
// especially the comment:
// https://stackoverflow.com/questions/2573834/c-convert-string-or-char-to-wstring-or-wchar-t#comment110447503_18597384
#ifdef _WIN32
#pragma warning(push, 0)
#include <windows.h>
#include <limits>
#include <cstring>
#pragma warning(pop)
#else
// NOTE (mristin):
// We use codecvt although it has been deprecated. There has been not
// suitable replacement proposed yet, so we simply stick to it
// until there is. See:
// https://stackoverflow.com/questions/42946335/deprecated-header-codecvt-replacement

#pragma warning(push, 0)
#include <codecvt>
#include <locale>
#pragma warning(pop)
#endif"""
        ),
        cpp_common.generate_namespace_opening(namespace),
        *_generate_concatenate_implementations_for_2_parts_and_above(),
        Stripped(
            f"""\
std::string WstringToUtf8(const std::wstring& text) {{
{I}#ifdef _WIN32
{I}// Inspired by:
{I}// https://stackoverflow.com/a/69410299/1600678

{I}if (text.empty()) {{
{II}return "";
{I}}}

{I}// NOTE (mristin):
{I}// We put `max` into parentheses to avoid conflicts with
{I}// <windows.h> `max` macro, see:
{I}// https://stackoverflow.com/questions/11544073/how-do-i-deal-with-the-max-macro-in-windows-h-colliding-with-max-in-std

{I}const size_t text_size = text.size();
{I}if (
{II}text_size
{II}> static_cast<size_t>(
{III}(std::numeric_limits<int>::max)()
{II})
{I}) {{
{II}throw std::out_of_range(
{III}common::Concat(
{IIII}"The size of the text to be converted to UTF-8, ",
{IIII}std::to_string(text_size),
{IIII}", exceeds the maximum int value ",
{IIII}std::to_string((std::numeric_limits<int>::max)())
{III})
{II});
{I}}}
{I}const int text_size_int = static_cast<int>(text_size);

{I}const auto size_needed = WideCharToMultiByte(
{II}CP_UTF8,
{II}0,
{II}&(text[0]),
{II}text_size_int,
{II}nullptr,
{II}0,
{II}nullptr,
{II}nullptr
{I});

{I}if (size_needed <= 0) {{
{II}throw std::runtime_error(
{III}"WideCharToMultiByte() failed: " + std::to_string(size_needed)
{II});
{I}}}

{I}std::string result(size_needed, 0);

{I}WideCharToMultiByte(
{II}CP_UTF8,
{II}0,
{II}&(text[0]),
{II}text_size_int,
{II}&(result[0]),
{II}size_needed,
{II}nullptr,
{II}nullptr
{I});

{I}return result;
{I}#else
{I}// NOTE (mristin):
{I}// We use codecvt although it has been deprecated. There has been not
{I}// suitable replacement proposed yet, so we simply stick to it
{I}// until there is. See:
{I}// https://stackoverflow.com/questions/42946335/deprecated-header-codecvt-replacement

{I}std::wstring_convert<std::codecvt_utf8<wchar_t> > conv;
{I}return conv.to_bytes(text.data());
{I}#endif
}}"""
        ),
        Stripped(
            f"""\
std::wstring Utf8ToWstring(
{I}const char* utf8_text,
{I}size_t utf8_text_size
) {{
{I}if (utf8_text_size == 0) {{
{II}return std::wstring();
{I}}}

{I}#ifdef _WIN32
{I}// NOTE (mristin):
{I}// We have to use MultiByteToWideChar from <windows.h> on Windows
{I}// as std::codecvt is not robust enough on Windows and produces invalid UTF-16
{I}// sequences as std::wstring. See:
{I}// https://stackoverflow.com/questions/2573834/c-convert-string-or-char-to-wstring-or-wchar-t,
{I}// especially the comment:
{I}// https://stackoverflow.com/questions/2573834/c-convert-string-or-char-to-wstring-or-wchar-t#comment110447503_18597384

{I}// Inspired by:
{I}// https://stackoverflow.com/a/69410299/1600678

{I}if (utf8_text_size == std::string::npos) {{
{II}utf8_text_size = strlen(utf8_text);
{I}}}

{I}// NOTE (mristin):
{I}// We put `max` into parentheses to avoid conflicts with
{I}// <windows.h> `max` macro, see:
{I}// https://stackoverflow.com/questions/11544073/how-do-i-deal-with-the-max-macro-in-windows-h-colliding-with-max-in-std

{I}if (
{II}utf8_text_size
{II}> static_cast<size_t>(
{III}(std::numeric_limits<int>::max)()
{II})
{I}) {{
{II}throw std::out_of_range(
{III}common::Concat(
{IIII}"The size of the UTF-8 text to be converted to wide string, ",
{IIII}std::to_string(utf8_text_size),
{IIII}", exceeds the maximum int value ",
{IIII}std::to_string((std::numeric_limits<int>::max)())
{III})
{II});
{I}}}
{I}const int utf8_text_size_int = static_cast<int>(utf8_text_size);

{I}const auto size_needed = MultiByteToWideChar(
{II}CP_UTF8,
{II}0,
{II}utf8_text,
{II}utf8_text_size_int,
{II}nullptr,
{II}0
{I});
{I}if (size_needed <= 0) {{
{II}throw std::runtime_error(
{III}"MultiByteToWideChar() failed: " + std::to_string(size_needed)
{II});
{I}}}

{I}std::wstring result(size_needed, 0);

{I}MultiByteToWideChar(
{II}CP_UTF8,
{II}0,
{II}utf8_text,
{II}utf8_text_size_int,
{II}&(result[0]),
{II}size_needed
{I});

{I}return result;

{I}#else
{I}// NOTE (mristin):
{I}// We use codecvt although it has been deprecated. There has been not
{I}// suitable replacement proposed yet, so we simply stick to it
{I}// until there is. See:
{I}// https://stackoverflow.com/questions/42946335/deprecated-header-codecvt-replacement

{I}std::wstring_convert<std::codecvt_utf8<wchar_t>,wchar_t> conv;
{I}return conv.from_bytes(utf8_text);
{I}#endif
}}"""
        ),
        Stripped(
            f"""\
std::wstring Utf8ToWstring(const std::string& utf8_text) {{
{I}return Utf8ToWstring(&(utf8_text[0]), utf8_text.size());
}}"""
        ),
        *(
            _generate_string_helper_definitions(symbol_table)
            if (
                intermediate_uses.len_slicing_or_find(symbol_table)
                or intermediate_uses.lstrip_call(symbol_table)
            )
            else []
        ),
        *([FLOOR_MOD_DEFINITION] if intermediate_uses.modulo(symbol_table) else []),
        *(
            [PARSE_SAFE_INT_DEFINITION]
            if intermediate_uses.int_call(symbol_table)
            else []
        ),
        *(
            [_LESS_BY_CODE_POINTS_DEFINITION]
            if intermediate_uses.sets_of_strings_in_properties(symbol_table)
            else []
        ),
        cpp_common.generate_namespace_closing(namespace),
        cpp_common.WARNING,
    ]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate_header.__doc__ is not None
cpp_common.assert_module_docstring_and_generate_header_consistent(
    module_doc=__doc__, generate_header_doc=generate_header.__doc__
)

assert generate_implementation.__doc__ is not None
cpp_common.assert_module_docstring_and_generate_implementation_consistent(
    module_doc=__doc__, generate_implementation_doc=generate_implementation.__doc__
)
