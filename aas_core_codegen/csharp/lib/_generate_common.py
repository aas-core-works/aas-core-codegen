"""Generate the helpers shared by the transpiled code in the other modules."""

import io
import textwrap
from typing import Final, List

from aas_core_codegen import intermediate
from aas_core_codegen.common import Stripped
from aas_core_codegen.csharp import common as csharp_common
from aas_core_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
)


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


def _generate_string_helpers() -> Stripped:
    """
    Generate the helpers for ``len``, slicing strings and ``find``.

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
{I}/// <summary>
{I}/// Check whether a surrogate pair starts at <paramref name="offset" />
{I}/// in <paramref name="text" />.
{I}/// </summary>
{I}private static bool IsSurrogatePairAt(string text, int offset)
{I}{{
{II}return (
{III}offset + 1 < text.Length
{III}&& char.IsHighSurrogate(text[offset])
{III}&& char.IsLowSurrogate(text[offset + 1])
{II});
{I}}}

{I}/// <summary>
{I}/// Count the characters of <paramref name="text" /> between the UTF-16
{I}/// offsets <paramref name="startOffset" /> and <paramref name="endOffset" />.
{I}/// </summary>
{I}private static int CountCharacters(
{II}string text,
{II}int startOffset,
{II}int endOffset
{I})
{I}{{
{II}int count = 0;
{II}int offset = startOffset;
{II}while (offset < endOffset)
{II}{{
{III}offset += IsSurrogatePairAt(text, offset) ? 2 : 1;
{III}count++;
{II}}}

{II}return count;
{I}}}

{I}/// <summary>
{I}/// Compute the UTF-16 offset of the character at <paramref name="position" />
{I}/// in <paramref name="text" />.
{I}/// </summary>
{I}private static int OffsetOf(string text, int position)
{I}{{
{II}int offset = 0;
{II}for (int i = 0; i < position; i++)
{II}{{
{III}offset += IsSurrogatePairAt(text, offset) ? 2 : 1;
{II}}}

{II}return offset;
{I}}}

{I}/// <summary>
{I}/// Resolve <paramref name="position" /> in a string of
{I}/// <paramref name="length" /> as Python does in slicing.
{I}/// </summary>
{I}/// <remarks>
{I}/// A negative position counts from the end, and the positions out of range
{I}/// are clamped to the string.
{I}/// </remarks>
{I}private static int ResolvePosition(long position, int length)
{I}{{
{II}if (position < 0)
{II}{{
{III}return (int)System.Math.Max(position + length, 0);
{II}}}

{II}return (int)System.Math.Min(position, length);
{I}}}

{I}/// <summary>
{I}/// Count the characters (code points) of <paramref name="text" />.
{I}/// </summary>
{I}/// <remarks>
{I}/// We follow the Python implementation of <c>len</c>, since Python is
{I}/// the language of the meta-model specifications. Hence, a character beyond
{I}/// the Basic Multilingual Plane counts as one, unlike in <c>text.Length</c>.
{I}/// </remarks>
{I}public static int Len(string text)
{I}{{
{II}return CountCharacters(text, 0, text.Length);
{I}}}

{I}/// <summary>
{I}/// Slice <paramref name="text" /> from <paramref name="start" /> up to
{I}/// <paramref name="end" />, exclusive.
{I}/// </summary>
{I}/// <remarks>
{I}/// We follow the Python implementation of slicing, since Python is
{I}/// the language of the meta-model specifications. Hence, the positions count
{I}/// the characters (code points), a negative position counts from the end,
{I}/// the positions out of range are clamped to the string, and the slice is
{I}/// empty if <paramref name="start" /> is not before <paramref name="end" />.
{I}/// If <paramref name="end" /> is not given, we slice up to the end of
{I}/// <paramref name="text" />.
{I}/// </remarks>
{I}public static string Slice(string text, long start, long? end = null)
{I}{{
{II}int length = Len(text);
{II}int theStart = ResolvePosition(start, length);
{II}int theEnd = end is null
{III}? length
{III}: ResolvePosition(end.Value, length);

{II}if (theStart >= theEnd)
{II}{{
{III}return "";
{II}}}

{II}int startOffset = OffsetOf(text, theStart);
{II}int endOffset = OffsetOf(text, theEnd);
{II}return text.Substring(startOffset, endOffset - startOffset);
{I}}}

{I}/// <summary>
{I}/// Find the first <paramref name="sub" /> in <paramref name="text" /> from
{I}/// <paramref name="start" /> on.
{I}/// </summary>
{I}/// <remarks>
{I}/// We follow the Python implementation of <c>str.find</c>, since Python is
{I}/// the language of the meta-model specifications. Hence, the positions count
{I}/// the characters (code points), a negative <paramref name="start" /> counts
{I}/// from the end, and a <paramref name="start" /> beyond the end of
{I}/// <paramref name="text" /> gives -1. We compare the strings ordinally.
{I}/// </remarks>
{I}/// <returns>
{I}/// The position of <paramref name="sub" /> in <paramref name="text" />,
{I}/// or -1 if not found
{I}/// </returns>
{I}public static long Find(string text, string sub, long start = 0)
{I}{{
{II}int length = Len(text);
{II}long theStart = start < 0
{III}? System.Math.Max(start + length, 0)
{III}: start;

{II}if (theStart > length)
{II}{{
{III}return -1;
{II}}}

{II}int startOffset = OffsetOf(text, (int)theStart);
{II}int offset = text.IndexOf(
{III}sub,
{III}startOffset,
{III}System.StringComparison.Ordinal
{II});

{II}if (offset == -1)
{II}{{
{III}return -1;
{II}}}

{II}return theStart + CountCharacters(text, startOffset, offset);
{I}}}
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

    if intermediate.uses_len_slicing_or_find(symbol_table):
        blocks.append(_generate_string_helpers())

    # NOTE (mristin):
    # We add the helper only if the meta-model uses the modulo so that we do not
    # clutter the code otherwise. The helper is public so that the clients can
    # rely on it, and so that we can unit-test it.
    if intermediate.uses_modulo(symbol_table):
        blocks.append(FLOOR_MOD)

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
