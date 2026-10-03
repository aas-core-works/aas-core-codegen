"""Generate the helpers shared by the transpiled code in the other modules."""

import io
import textwrap
from typing import Final, List

from aas_core_codegen import intermediate
from aas_core_codegen.common import Stripped, indent_but_first_line
from aas_core_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
)
from aas_core_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)
from aas_core_codegen.intermediate import uses as intermediate_uses


_TUPLE_HELPERS: Final[Stripped] = Stripped(
    f"""\
/// <summary>
/// Provide operations on tuples.
/// </summary>
public static class TupleHelpers
{{
{I}/// <summary>
{I}/// Count the items of <paramref name="tuple" />.
{I}/// </summary>
{I}public static int Len(System.Runtime.CompilerServices.ITuple tuple)
{I}{{
{II}return tuple.Length;
{I}}}
}}  // public static class TupleHelpers"""
)


def _generate_string_helpers(symbol_table: intermediate.SymbolTable) -> Stripped:
    """
    Generate the helpers for ``len``, slicing strings, ``find`` and ``lstrip``.

    The helpers follow the Python implementation, since Python is the language of
    the meta-model specifications. Hence, the lengths and the positions count
    the characters (code points), while the C# strings count the UTF-16 code
    units, where a character beyond the Basic Multilingual Plane takes two
    of them (a surrogate pair). Moreover, the native ``Substring`` and ``IndexOf``
    throw on the positions out of range, and do not count the negative positions
    from the end. We also accept the positions as ``long``'s, since our integers
    are ``long``'s in C#.
    """
    # NOTE (mristin):
    # We count a lone surrogate as a character of its own, as Python does. We do
    # not check whether ``IndexOf`` matches in the middle of a surrogate pair, as
    # that could only happen if the searched text started or ended with a lone
    # surrogate.
    members = [
        Stripped(
            f"""\
/// <summary>
/// Check whether a surrogate pair starts at <paramref name="offset" />
/// in <paramref name="text" />.
/// </summary>
private static bool IsSurrogatePairAt(string text, int offset)
{{
{I}return (
{II}offset + 1 < text.Length
{II}&& char.IsHighSurrogate(text[offset])
{II}&& char.IsLowSurrogate(text[offset + 1])
{I});
}}"""
        )
    ]  # type: List[Stripped]

    if intermediate_uses.len_slicing_or_find(symbol_table):
        members.append(
            Stripped(
                f"""\
/// <summary>
/// Count the characters of <paramref name="text" /> between the UTF-16
/// offsets <paramref name="startOffset" /> and <paramref name="endOffset" />.
/// </summary>
private static int CountCharacters(
{I}string text,
{I}int startOffset,
{I}int endOffset
)
{{
{I}int count = 0;
{I}int offset = startOffset;
{I}while (offset < endOffset)
{I}{{
{II}offset += IsSurrogatePairAt(text, offset) ? 2 : 1;
{II}count++;
{I}}}

{I}return count;
}}

/// <summary>
/// Compute the UTF-16 offset of the character at <paramref name="position" />
/// in <paramref name="text" />.
/// </summary>
private static int OffsetOf(string text, int position)
{{
{I}int offset = 0;
{I}for (int i = 0; i < position; i++)
{I}{{
{II}offset += IsSurrogatePairAt(text, offset) ? 2 : 1;
{I}}}

{I}return offset;
}}

/// <summary>
/// Resolve <paramref name="position" /> in a string of
/// <paramref name="length" /> as Python does in slicing.
/// </summary>
/// <remarks>
/// A negative position counts from the end, and the positions out of range
/// are clamped to the string.
/// </remarks>
private static int ResolvePosition(long position, int length)
{{
{I}if (position < 0)
{I}{{
{II}return (int)System.Math.Max(position + length, 0);
{I}}}

{I}return (int)System.Math.Min(position, length);
}}

/// <summary>
/// Count the characters (code points) of <paramref name="text" />.
/// </summary>
/// <remarks>
/// We follow the Python implementation of <c>len</c>, since Python is
/// the language of the meta-model specifications. Hence, a character beyond
/// the Basic Multilingual Plane counts as one, unlike in <c>text.Length</c>.
/// </remarks>
public static int Len(string text)
{{
{I}return CountCharacters(text, 0, text.Length);
}}

/// <summary>
/// Slice <paramref name="text" /> from <paramref name="start" /> up to
/// <paramref name="end" />, exclusive.
/// </summary>
/// <remarks>
/// We follow the Python implementation of slicing, since Python is
/// the language of the meta-model specifications. Hence, the positions count
/// the characters (code points), a negative position counts from the end,
/// the positions out of range are clamped to the string, and the slice is
/// empty if <paramref name="start" /> is not before <paramref name="end" />.
/// If <paramref name="end" /> is not given, we slice up to the end of
/// <paramref name="text" />.
/// </remarks>
public static string Slice(string text, long start, long? end = null)
{{
{I}int length = Len(text);
{I}int theStart = ResolvePosition(start, length);
{I}int theEnd = end is null
{II}? length
{II}: ResolvePosition(end.Value, length);

{I}if (theStart >= theEnd)
{I}{{
{II}return "";
{I}}}

{I}int startOffset = OffsetOf(text, theStart);
{I}int endOffset = OffsetOf(text, theEnd);
{I}return text.Substring(startOffset, endOffset - startOffset);
}}

/// <summary>
/// Find the first <paramref name="sub" /> in <paramref name="text" /> from
/// <paramref name="start" /> on.
/// </summary>
/// <remarks>
/// We follow the Python implementation of <c>str.find</c>, since Python is
/// the language of the meta-model specifications. Hence, the positions count
/// the characters (code points), a negative <paramref name="start" /> counts
/// from the end, and a <paramref name="start" /> beyond the end of
/// <paramref name="text" /> gives -1. We compare the strings ordinally.
/// </remarks>
/// <returns>
/// The position of <paramref name="sub" /> in <paramref name="text" />,
/// or -1 if not found
/// </returns>
public static long Find(string text, string sub, long start = 0)
{{
{I}int length = Len(text);
{I}long theStart = start < 0
{II}? System.Math.Max(start + length, 0)
{II}: start;

{I}if (theStart > length)
{I}{{
{II}return -1;
{I}}}

{I}int startOffset = OffsetOf(text, (int)theStart);
{I}int offset = text.IndexOf(
{II}sub,
{II}startOffset,
{II}System.StringComparison.Ordinal
{I});

{I}if (offset == -1)
{I}{{
{II}return -1;
{I}}}

{I}return theStart + CountCharacters(text, startOffset, offset);
}}"""
            )
        )

    if intermediate_uses.lstrip_call(symbol_table):
        members.append(
            Stripped(
                f"""\
/// <summary>
/// Strip the longest prefix of <paramref name="text" /> which consists only
/// of the characters listed in <paramref name="chars" />.
/// </summary>
/// <remarks>
/// We follow the Python implementation of <c>str.lstrip</c>, since Python is
/// the language of the meta-model specifications. Hence, we strip
/// the characters (code points), and not the UTF-16 code units. Otherwise,
/// we would strip a half of a surrogate pair if a character in
/// <paramref name="chars" /> shared the high surrogate with it.
/// </remarks>
public static string LStrip(string text, string chars)
{{
{I}int offset = 0;
{I}while (offset < text.Length)
{I}{{
{II}int width = IsSurrogatePairAt(text, offset) ? 2 : 1;

{II}bool found = false;
{II}int charsOffset = 0;
{II}while (charsOffset < chars.Length)
{II}{{
{III}int charsWidth = IsSurrogatePairAt(chars, charsOffset) ? 2 : 1;
{III}if (
{IIII}charsWidth == width
{IIII}&& string.CompareOrdinal(chars, charsOffset, text, offset, width) == 0
{III})
{III}{{
{IIII}found = true;
{IIII}break;
{III}}}

{III}charsOffset += charsWidth;
{II}}}

{II}if (!found)
{II}{{
{III}break;
{II}}}

{II}offset += width;
{I}}}

{I}return text.Substring(offset);
}}"""
            )
        )

    members_joined = "\n\n".join(members)

    return Stripped(
        f"""\
/// <summary>
/// Provide string operations which follow the Python implementation, since
/// Python is the language of the meta-model specifications.
/// </summary>
/// <remarks>
/// The lengths and the positions count the characters (code points), and not
/// the UTF-16 code units of the C# strings. Hence, a character beyond the Basic
/// Multilingual Plane counts as one, though it takes two UTF-16 code units
/// (a surrogate pair).
/// </remarks>
public static class StringHelpers
{{
{I}{indent_but_first_line(members_joined, I)}
}}  // public static class StringHelpers"""
    )


#: Helper to compute the remainder of the floored division as in Python.
#:
#: We deliberately do not transpile the modulo to the native C# operator ``%``.
#: C# truncates the division towards zero so that its remainder takes the sign of
#: the dividend (``-7 % 3 == -1``). The meta-model is written in Python where
#: the division is floored so that the remainder takes the sign of the divisor
#: (``-7 % 3 == 2``). The two only coincide when the operands have the same sign,
#: but the invariants must behave the same in all the SDKs for all the inputs.
FLOOR_MOD = Stripped(
    f"""\
/// <summary>
/// Compute the remainder of the floored division of <paramref name="dividend" />
/// by <paramref name="divisor" />.
/// </summary>
/// <remarks>
/// <para>
/// The remainder takes the sign of the divisor, as the modulo in Python,
/// in which the meta-model is written.
/// </para>
/// <para>
/// We deliberately do not use the native operator <c>%</c> which truncates
/// the division towards zero so that its remainder takes the sign of
/// the dividend. For example, <c>-7 % 3 == -1</c> in C#, while
/// <c>-7 % 3 == 2</c> in Python. The two only coincide when the operands have
/// the same sign, but the invariants must behave the same in all the SDKs for
/// all the inputs.
/// </para>
/// <para>
/// The <paramref name="divisor" /> must not be zero.
/// </para>
/// </remarks>
public static long FloorMod(long dividend, long divisor)
{{
{I}// NOTE: The native long.MinValue % -1 overflows in C#, while
{I}// every number is divisible by -1 without a remainder.
{I}if (divisor == -1)
{I}{{
{II}return 0;
{I}}}

{I}long remainder = dividend % divisor;
{I}if (remainder != 0 && (remainder < 0) != (divisor < 0))
{I}{{
{II}remainder += divisor;
{I}}}

{I}return remainder;
}}"""
)


#: Parse a text as a safe integer; this is how we transpile the built-in ``int``.
#:
#: We do not use the native ``long.Parse`` as it depends on the culture, and
#: accepts the numbers beyond the safe integers. The safe integers are the integers
#: which a double-precision floating-point number represents exactly. We limit
#: ourselves to them so that all the SDKs behave the same, including TypeScript,
#: which represents the integers as ``number``.
PARSE_SAFE_INT = Stripped(
    f"""\
/// <summary>
/// Parse <paramref name="text" /> as a safe integer.
/// </summary>
/// <remarks>
/// <para>
/// The meta-model calls <c>int</c> on strings, and this is its transpilation.
/// </para>
/// <para>
/// We accept only an optional sign followed by the ASCII digits, and only
/// the safe integers, <em>i.e.</em>, the integers within <c>-(2^53 - 1)</c>
/// and <c>2^53 - 1</c>, which a double-precision floating-point number
/// represents exactly. This way, all the SDKs behave the same.
/// </para>
/// </remarks>
/// <param name="text">to be parsed</param>
/// <returns>the parsed integer</returns>
/// <exception cref="System.ArgumentException">
/// Thrown if <paramref name="text" /> is not a safe integer.
/// </exception>
public static long ParseSafeInt(string text)
{{
{I}int start = 0;
{I}bool negative = false;
{I}if (text.Length > 0 && (text[0] == '+' || text[0] == '-'))
{I}{{
{II}negative = text[0] == '-';
{II}start = 1;
{I}}}

{I}if (start == text.Length)
{I}{{
{II}throw new System.ArgumentException(
{III}"Expected an optional sign followed by the ASCII digits, " +
{III}$"but got: {{text}}");
{I}}}

{I}long value = 0;
{I}for (int i = start; i < text.Length; i++)
{I}{{
{II}char character = text[i];
{II}if (character < '0' || character > '9')
{II}{{
{III}throw new System.ArgumentException(
{IIII}"Expected an optional sign followed by the ASCII digits, " +
{IIII}$"but got: {{text}}");
{II}}}

{II}// NOTE: The value is at most 2^53 - 1 before this step, so it can not
{II}// overflow a long.
{II}value = value * 10 + (character - '0');

{II}// NOTE: This is 2^53 - 1.
{II}if (value > 9007199254740991L)
{II}{{
{III}throw new System.ArgumentException(
{IIII}$"Expected a safe integer, but got a text out of its range: {{text}}");
{II}}}
{I}}}

{I}return negative ? -value : value;
}}"""
)


def _generate_set_helpers(symbol_table: intermediate.SymbolTable) -> Stripped:
    """
    Generate the helpers which sort the items of the set properties.

    The set properties are serialized sorted, in the same order in all the SDKs:
    ``false`` before ``true``, the integers numerically, and the strings and
    the serialized values of the enumeration literals by their code points.
    The C# strings, however, compare by their UTF-16 code units, which sort
    the characters beyond the Basic Multilingual Plane (surrogate pairs) before
    the characters from U+E000 to U+FFFF.
    """
    members = [
        Stripped(
            f"""\
/// <summary>
/// Decode the code point at <paramref name="offset" /> in
/// <paramref name="text" />.
/// </summary>
/// <remarks>
/// A lone surrogate is decoded as a code point of its own.
/// </remarks>
private static int CodePointAt(string text, int offset)
{{
{I}return (
{II}offset + 1 < text.Length
{II}&& char.IsHighSurrogate(text[offset])
{II}&& char.IsLowSurrogate(text[offset + 1])
{I})
{II}? char.ConvertToUtf32(text[offset], text[offset + 1])
{II}: text[offset];
}}"""
        ),
        Stripped(
            f"""\
/// <summary>
/// Compare <paramref name="that" /> and <paramref name="other" /> by their
/// code points.
/// </summary>
/// <remarks>
/// Unlike <see cref="string.CompareOrdinal(string, string)" />, which compares
/// the UTF-16 code units, this comparison sorts the characters beyond
/// the Basic Multilingual Plane after all the others.
/// </remarks>
public static int CompareByCodePoints(string that, string other)
{{
{I}int length = System.Math.Min(that.Length, other.Length);

{I}int offset = 0;
{I}while (offset < length && that[offset] == other[offset])
{I}{{
{II}offset++;
{I}}}

{I}if (offset == length)
{I}{{
{II}return that.Length.CompareTo(other.Length);
{I}}}

{I}// NOTE: We might have stopped in the middle of a surrogate pair.
{I}if (
{II}offset > 0
{II}&& char.IsHighSurrogate(that[offset - 1])
{II}&& (
{III}char.IsLowSurrogate(that[offset])
{III}|| char.IsLowSurrogate(other[offset])
{II})
{I})
{I}{{
{II}offset--;
{I}}}

{I}return CodePointAt(that, offset).CompareTo(CodePointAt(other, offset));
}}"""
        ),
    ]  # type: List[Stripped]

    for enumeration in intermediate_uses.enumerations_in_set_properties(symbol_table):
        enum_name = csharp_naming.enum_name(enumeration.name)
        # NOTE (mristin):
        # See the note above ``csharp_common.rank_of_enumeration_name`` why these
        # names can never coincide with the names of the fixed helpers.
        rank_name = csharp_common.rank_of_enumeration_name(enumeration)
        compare_name = csharp_common.compare_by_rank_of_enumeration_name(enumeration)

        # NOTE (mristin):
        # Python compares the strings by their code points, so we can rank
        # the literals here once instead of comparing their values at run time.
        sorted_literals = sorted(
            enumeration.literals, key=lambda a_literal: a_literal.value
        )

        cases = []  # type: List[str]
        for rank, literal in enumerate(sorted_literals):
            literal_name = csharp_naming.enum_literal_name(literal.name)
            cases.append(
                f"""\
case {enum_name}.{literal_name}:
{I}return {rank};  // {csharp_common.string_literal(literal.value)}"""
            )

        cases.append(
            f"""\
default:
{I}return {len(sorted_literals)};"""
        )

        cases_joined = "\n".join(cases)

        members.append(
            Stripped(
                f"""\
/// <summary>
/// Rank <paramref name="literal" /> by its serialized value in code points.
/// </summary>
private static int {rank_name}({enum_name} literal)
{{
{I}switch (literal)
{I}{{
{II}{indent_but_first_line(cases_joined, II)}
{I}}}
}}"""
            )
        )

        members.append(
            Stripped(
                f"""\
/// <summary>
/// Compare the literals of <see cref="{enum_name}" /> by their serialized
/// values in code points.
/// </summary>
/// <remarks>
/// The invalid literals, which have no serialized value, come last.
/// </remarks>
public static int {compare_name}({enum_name} that, {enum_name} other)
{{
{I}return {rank_name}(that).CompareTo({rank_name}(other));
}}"""
            )
        )

    members.append(
        Stripped(
            f"""\
/// <summary>
/// Copy <paramref name="items" /> into a new list sorted by
/// <paramref name="comparison" />.
/// </summary>
public static System.Collections.Generic.List<T> Sorted<T>(
{I}System.Collections.Generic.IEnumerable<T> items,
{I}System.Comparison<T> comparison)
{{
{I}var result = new System.Collections.Generic.List<T>(items);
{I}result.Sort(comparison);
{I}return result;
}}"""
        )
    )

    members_joined = "\n\n".join(members)

    return Stripped(
        f"""\
/// <summary>
/// Sort the items of the sets, so that they are serialized in the same order
/// in all the SDKs.
/// </summary>
public static class SetHelpers
{{
{I}{indent_but_first_line(members_joined, I)}
}}  // public static class SetHelpers"""
    )


def generate(
    symbol_table: intermediate.SymbolTable,
    namespace: csharp_common.NamespaceIdentifier,
) -> str:
    """
    Generate the helpers shared by the transpiled code in the other modules.

    The transpiled code lives both in the verification and in the methods of
    the types, so the helpers can live in neither of them.

    The ``namespace`` defines the base C# namespace of the generated code.
    """
    blocks = [_TUPLE_HELPERS]  # type: List[Stripped]

    if intermediate_uses.len_slicing_or_find(
        symbol_table
    ) or intermediate_uses.lstrip_call(symbol_table):
        blocks.append(_generate_string_helpers(symbol_table))

    if intermediate_uses.set_properties(symbol_table):
        blocks.append(_generate_set_helpers(symbol_table))

    # NOTE (mristin):
    # We add the helper only if the meta-model uses the modulo so that we do not
    # clutter the code otherwise. The helper is public so that the clients can
    # rely on it, and so that we can unit-test it.
    if intermediate_uses.modulo(symbol_table):
        blocks.append(FLOOR_MOD)

    # NOTE (mristin):
    # We add the helper only if the meta-model calls int so that we do not
    # clutter the code otherwise.
    if intermediate_uses.int_call(symbol_table):
        blocks.append(PARSE_SAFE_INT)

    writer = io.StringIO()
    writer.write(csharp_common.WARNING)
    writer.write(
        f"""


namespace {namespace}
{{
{I}/// <summary>
{I}/// Provide the helpers shared by the transpiled code in the other modules.
{I}/// </summary>
{I}public static class {csharp_common.COMMON_CLASS}
{I}{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, II))

    writer.write(f"\n{I}}}  // public static class {csharp_common.COMMON_CLASS}")
    writer.write(f"\n}}  // namespace {namespace}\n\n")
    writer.write(csharp_common.WARNING)
    writer.write("\n")

    return writer.getvalue()
