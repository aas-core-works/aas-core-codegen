"""Generate code of common functionality."""

import io
from typing import Final, List, Sequence

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Stripped,
    indent_but_first_line,
)
from aas_core_codegen.golang import (
    common as golang_common,
    transpilation as golang_transpilation,
)
from aas_core_codegen.golang.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
)
from aas_core_codegen.intermediate import uses as intermediate_uses


def _generate_tuple_struct(arity: int) -> Stripped:
    """Generate the generic struct representing a tuple of the given ``arity``."""
    type_params = ", ".join(f"T{i + 1} any" for i in range(arity))
    type_args = ", ".join(f"T{i + 1}" for i in range(arity))
    fields = "\n".join(f"Item{i + 1} T{i + 1}" for i in range(arity))

    name = f"Tuple{arity}"

    return Stripped(
        f"""\
// Represent a fixed-size heterogeneous tuple of {arity} item(s).
type {name}[{type_params}] struct {{
{I}{indent_but_first_line(fields, I)}
}}

// Count the items of the tuple.
func (tuple {name}[{type_args}]) Len() int {{
{I}return {arity}
}}"""
    )


#: Check if any or all the items of a set, or the keys of a map, satisfy the condition
SOME_AND_ALL_KEYS: Final[Sequence[Stripped]] = [
    Stripped(
        f"""\
// Check if any of the keys of the map satisfy the condition.
//
// A set is represented as a map to empty structs, so this checks its items.
func SomeKey[K comparable, V any](condition func(K) bool, m map[K]V) bool {{
{I}for k := range m {{
{II}if condition(k) {{
{III}return true
{II}}}
{I}}}
{I}return false
}}"""
    ),
    Stripped(
        f"""\
// Check if all the keys of the map satisfy the condition.
//
// A set is represented as a map to empty structs, so this checks its items.
func AllKeys[K comparable, V any](condition func(K) bool, m map[K]V) bool {{
{I}for k := range m {{
{II}if !condition(k) {{
{III}return false
{II}}}
{I}}}
{I}return true
}}"""
    ),
]

#: Look up the values of a dictionary as in Python
MAP_LOOK_UPS: Final[Sequence[Stripped]] = [
    Stripped(
        f"""\
// Get the value of the key `k` in the map `m`, and panic if the key is missing.
//
// This is the index access of a dictionary in Python, which raises a `KeyError`
// if the key is missing, while the native index access gives the zero value.
func MapMustGet[K comparable, V any](m map[K]V, k K) V {{
{I}v, ok := m[k]
{I}if !ok {{
{II}panic("The key is missing in the map.")
{I}}}
{I}return v
}}"""
    ),
    Stripped(
        f"""\
// Get a pointer to a copy of the value of the key `k` in the map `m`, or nil
// if the key is missing.
//
// This is ``get`` of a dictionary in Python without a default for the values
// whose optionals are represented as pointers.
func MapGetPointer[K comparable, V any](m map[K]V, k K) *V {{
{I}v, ok := m[k]
{I}if !ok {{
{II}return nil
{I}}}
{I}return &v
}}"""
    ),
    Stripped(
        f"""\
// Get the value of the key `k` in the map `m`, or the `defaultValue` if the key
// is missing.
//
// This is ``get`` of a dictionary in Python with a default.
func MapGetOr[K comparable, V any](m map[K]V, k K, defaultValue V) V {{
{I}v, ok := m[k]
{I}if !ok {{
{II}return defaultValue
{I}}}
{I}return v
}}"""
    ),
]

#: Give a new set as the intersection or the difference of two sets, as in Python
SET_OPERATIONS: Final[Sequence[Stripped]] = [
    Stripped(
        f"""\
// Give a new set of the items which are both in `that` and in `other`.
func SetIntersection[K comparable](
{I}that map[K]struct{{}},
{I}other map[K]struct{{}},
) map[K]struct{{}} {{
{I}result := make(map[K]struct{{}})
{I}for k := range that {{
{II}if _, ok := other[k]; ok {{
{III}result[k] = struct{{}}{{}}
{II}}}
{I}}}
{I}return result
}}"""
    ),
    Stripped(
        f"""\
// Give a new set of the items which are in `that`, but not in `other`.
func SetDifference[K comparable](
{I}that map[K]struct{{}},
{I}other map[K]struct{{}},
) map[K]struct{{}} {{
{I}result := make(map[K]struct{{}})
{I}for k := range that {{
{II}if _, ok := other[k]; !ok {{
{III}result[k] = struct{{}}{{}}
{II}}}
{I}}}
{I}return result
}}"""
    ),
]

#: Sort the items of a set, or the keys of a dictionary, in the order of their
#: serialization
SORTED_KEYS: Final[Sequence[Stripped]] = [
    Stripped(
        f"""\
// Collect the keys of the map `m` into a slice, sorted by `less`.
//
// A set is represented as a map to empty structs, so this gives its items.
// A nil map gives a nil slice, so that an absent optional set stays absent.
//
// We serialize the sets as arrays whose items are sorted, and the dictionaries
// with their keys sorted, in the same order in all the SDKs, see [LessBool]
// and [LessOrdered].
func SortedKeys[K comparable, V any](
{I}m map[K]V,
{I}less func(that K, other K) bool,
) []K {{
{I}if m == nil {{
{II}return nil
{I}}}

{I}result := make([]K, 0, len(m))
{I}for k := range m {{
{II}result = append(result, k)
{I}}}

{I}sort.Slice(
{II}result,
{II}func(i, j int) bool {{
{III}return less(result[i], result[j])
{II}}},
{I})
{I}return result
}}"""
    ),
    Stripped(
        f"""\
// Check whether `that` comes before `other`, where false comes before true.
func LessBool(that bool, other bool) bool {{
{I}return !that && other
}}"""
    ),
    Stripped(
        f"""\
// Check whether `that` comes before `other`.
//
// The integers are compared numerically, and the strings byte by byte, which
// is the order of their code points, as the strings are encoded in UTF-8.
func LessOrdered[T int64 | string](that T, other T) bool {{
{I}return that < other
}}"""
    ),
]

#: Helper to compute the remainder of the floored division as in Python.
#:
#: We deliberately do not transpile the modulo to the native Go operator ``%``.
#: Go truncates the division towards zero so that its remainder takes the sign of
#: the dividend (``-7 % 3 == -1``). The meta-model is written in Python where
#: the division is floored so that the remainder takes the sign of the divisor
#: (``-7 % 3 == 2``). The two only coincide when the operands have the same sign,
#: but the invariants must behave the same in all the SDKs for all the inputs.
#:
#: Unlike C# or Java, Go defines the remainder of the smallest 64-bit integer by -1
#: as zero (see the section "Arithmetic operators" of the Go specification), so we
#: do not need a special guard for it.
#:
#: Mind that we must not mention the package ``math`` qualified in the comments,
#: as the imports are detected by
#: :py:func:`aas_core_codegen.golang.common.names_package`, and an unused import
#: does not compile in Go.
FLOOR_MOD = Stripped(
    f"""\
// {golang_transpilation.FLOOR_MOD_FUNCTION_NAME} computes the remainder of the floored division of dividend
// by divisor.
//
// The remainder takes the sign of the divisor, as the modulo in Python,
// in which the meta-model is written.
//
// We deliberately do not use the native operator `%` which truncates the division
// towards zero so that its remainder takes the sign of the dividend. For example,
// `-7 % 3 == -1` in Go, while `-7 % 3 == 2` in Python. The two only coincide when
// the operands have the same sign, but the invariants must behave the same in all
// the SDKs for all the inputs.
//
// The divisor must not be zero.
func {golang_transpilation.FLOOR_MOD_FUNCTION_NAME}(dividend, divisor int64) int64 {{
{I}// NOTE: Go defines the remainder of the smallest int64 by -1 as zero,
{I}// so we need no special guard for that case.
{I}remainder := dividend % divisor
{I}if remainder != 0 && (remainder < 0) != (divisor < 0) {{
{II}remainder += divisor
{I}}}
{I}return remainder
}}"""
)

#: Helper to compute the absolute value of a 64-bit signed integer.
#:
#: Go provides no absolute value of integers in its standard library, as ``math.Abs``
#: works only on ``float64``. Converting to ``float64`` and back would lose
#: precision for large integers.
#:
#: Mind that we must not mention the package ``math`` qualified in the comments,
#: as the imports are detected by
#: :py:func:`aas_core_codegen.golang.common.names_package`, and an unused import
#: does not compile in Go.
ABS_INT64 = Stripped(
    f"""\
// {golang_transpilation.ABS_INT64_FUNCTION_NAME} computes the absolute value of x.
//
// The Go standard library provides the absolute value only for floating-point
// numbers, so we provide our own for 64-bit integers.
//
// The absolute value of the smallest int64 overflows and is the smallest int64
// itself, as it can not be represented as a positive int64.
func {golang_transpilation.ABS_INT64_FUNCTION_NAME}(x int64) int64 {{
{I}if x < 0 {{
{II}return -x
{I}}}
{I}return x
}}"""
)


#: Helper to parse a string as a safe integer, which transpiles the built-in ``int``.
#:
#: We deliberately do not use ``strconv.ParseInt`` directly, so that the helper
#: reads the same as in the other SDKs. We accept only an optional sign followed by
#: the ASCII digits, and only the safe integers, *i.e.*, the integers which
#: a double-precision floating-point number represents exactly. We limit ourselves
#: to the safe integers as TypeScript represents the integers as ``number``, and
#: the invariants must behave the same in all the SDKs.
#:
#: The accumulated value never overflows, as we check the bound after each digit,
#: and ten times the largest safe integer plus nine still fits into ``int64``.
PARSE_SAFE_INT = Stripped(
    f"""\
// {golang_transpilation.PARSE_SAFE_INT_FUNCTION_NAME} parses text as a safe integer.
//
// The meta-model calls `int` on strings, and this is its transpilation. We accept
// only an optional sign followed by the ASCII digits, and only the safe integers,
// i.e., the integers within -(2^53 - 1) and 2^53 - 1, which a double-precision
// floating-point number represents exactly. This way, all the SDKs behave the same.
//
// Panics if text is not a safe integer. The meta-model is expected to check
// the text before it calls `int`, so a panic signals a bug in the meta-model.
func {golang_transpilation.PARSE_SAFE_INT_FUNCTION_NAME}(text string) int64 {{
{I}digits := text
{I}negative := false
{I}if len(digits) > 0 && (digits[0] == '+' || digits[0] == '-') {{
{II}negative = digits[0] == '-'
{II}digits = digits[1:]
{I}}}

{I}if len(digits) == 0 {{
{II}panic(
{III}fmt.Sprintf(
{IIII}"Expected an optional sign followed by the ASCII digits, but got: %q",
{IIII}text,
{III}),
{II})
{I}}}

{I}var value int64
{I}for i := 0; i < len(digits); i++ {{
{II}digit := digits[i]
{II}if digit < '0' || digit > '9' {{
{III}panic(
{IIII}fmt.Sprintf(
{IIIII}"Expected an optional sign followed by the ASCII digits, but got: %q",
{IIIII}text,
{IIII}),
{III})
{II}}}

{II}value = value*10 + int64(digit-'0')

{II}// NOTE: This is 2^53 - 1.
{II}if value > 9007199254740991 {{
{III}panic(
{IIII}fmt.Sprintf(
{IIIII}"Expected a safe integer, but got a text out of its range: %q",
{IIIII}text,
{IIII}),
{III})
{II}}}
{I}}}

{I}if negative {{
{II}return -value
{I}}}
{I}return value
}}"""
)


# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable) -> str:
    """Generate code of common functionality."""
    # NOTE (mristin):
    # An unused import does not compile in Go, so we import only what the helpers
    # below need.
    import_lines = []  # type: List[str]
    if intermediate_uses.int_call(symbol_table):
        import_lines.append(f'{I}"fmt"')

    if intermediate_uses.set_properties(
        symbol_table
    ) or intermediate_uses.dict_properties(symbol_table):
        import_lines.append(f'{I}"sort"')

    import_lines.append(f'{I}"strings"')

    if intermediate_uses.len_slicing_or_find(symbol_table):
        import_lines.append(f'{I}"unicode/utf8"')

    import_lines_joined = "\n".join(import_lines)

    blocks = [
        Stripped(
            """\
// Package common provides common functions shared among the other packages.
package common"""
        ),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{import_lines_joined}
)"""
        ),
        Stripped(
            f"""\
func Concat(
{I}parts ...string,
) string {{
{I}b := new(strings.Builder)
{I}for _, part := range parts {{
{II}b.WriteString(part)
{I}}}
{I}return b.String()
}}"""
        ),
        Stripped(
            f"""\
// Check if the map contains the given key.
func MapContains[K comparable, V any](m map[K]V, k K) bool {{
{I}_, ok := m[k]
{I}return ok
}}"""
        ),
        Stripped(
            f"""\
// Check if any of the elements satisfy the condition.
func Some[V any](condition func(V) bool, l []V) bool {{
{I}ok := false
{I}for _, v := range l {{
{II}ok = ok || condition(v)
{I}}}
{I}return ok
}}"""
        ),
        Stripped(
            f"""\
// Check if all the elements satisfy the condition.
func All[V any](condition func(V) bool, l []V) bool {{
{I}for _, v := range l {{
{II}if !condition(v) {{
{III}return false
{II}}}
{I}}}
{I}return true
}}"""
        ),
        Stripped(
            f"""\
// Check if some of the elements in the given range satisfy the condition.
//
// The range is over the lengths (`int`) or over the integers (`int64`).
func SomeRange[T int | int64](condition func(T) bool, start T, end T) bool {{
{I}for i := start; i < end; i++ {{
{II}if condition(i) {{
{III}return true
{II}}}
{I}}}
{I}return false
}}"""
        ),
        Stripped(
            f"""\
// Check if all the elements in the given range satisfy the condition.
//
// The range is over the lengths (`int`) or over the integers (`int64`).
func AllRange[T int | int64](condition func(T) bool, start T, end T) bool {{
{I}for i := start; i < end; i++ {{
{II}if !condition(i) {{
{III}return false
{II}}}
{I}}}
{I}return true
}}"""
        ),
        Stripped(
            f"""\
// Copy the `value` to a new variable, and return the pointer to it.
//
// We represent the optional values which are not nilable, such as strings,
// numbers and enumeration literals, as pointers. Go does not allow to take
// the address of a literal or of an expression, such as `&"something"`
// or `&(x + 1)`, so we need a function to hold the value in a variable of its
// own. Moreover, taking the address of a variable directly, such as `&text`,
// would alias the variable, so that a later assignment to the variable would
// also change the value pointed to.
//
// Mind that Go infers `int` for an untyped integer constant, so you need to
// convert it explicitly, for example, `NewAndPointTo(int64(1))`.
func NewAndPointTo[T any](value T) *T {{
{I}return &value
}}"""
        ),
    ]  # type: List[Stripped]

    blocks.extend(
        _generate_tuple_struct(arity=arity)
        for arity in range(1, golang_common.MAX_TUPLE_ARITY + 1)
    )

    # NOTE (mristin):
    # The Go strings count the UTF-8 bytes, while Python counts the characters
    # (code points). Moreover, the native slicing panics on the positions out of
    # range, does not count the negative ones from the end, and ``strings.Index``
    # has no start. We need helpers which follow the Python implementation of
    # ``len``, slicing and ``str.find``. The helpers are generated only for
    # a meta-model which might take ``len`` of strings, slice them or call ``find``
    # on them.
    #
    # We walk over the byte offsets of the characters instead of converting
    # the strings to ``[]rune``, so that we neither copy the strings nor replace
    # the invalid UTF-8 bytes. Each invalid byte counts as a character of its own,
    # as in ``utf8.RuneCountInString`` and in the ``range`` loop over a string.
    if intermediate_uses.len_slicing_or_find(symbol_table):
        blocks.extend(
            [
                Stripped(
                    f"""\
// Resolve `position` in a string of `length` as Python does in slicing.
//
// A negative position counts from the end, and the positions out of range are
// clamped to the string.
func resolvePosition(position int64, length int) int {{
{I}if position < 0 {{
{II}position += int64(length)
{II}if position < 0 {{
{III}return 0
{II}}}
{II}return int(position)
{I}}}

{I}if position > int64(length) {{
{II}return length
{I}}}
{I}return int(position)
}}"""
                ),
                Stripped(
                    f"""\
// Compute the byte offset of the character at `position` in `text`.
//
// The `position` counts the characters (code points), and must not exceed
// the number of characters in `text`.
func byteOffsetOf(text string, position int) int {{
{I}count := 0
{I}for offset := range text {{
{II}if count == position {{
{III}return offset
{II}}}
{II}count++
{I}}}
{I}return len(text)
}}"""
                ),
                Stripped(
                    f"""\
// Count the characters (code points) of `text`.
//
// We follow the Python implementation of `len`, since Python is the language of
// the meta-model specifications. Hence, we count the characters instead of
// the UTF-8 bytes as the native `len` does.
func LenStr(text string) int {{
{I}return utf8.RuneCountInString(text)
}}"""
                ),
                Stripped(
                    f"""\
// Slice `text` from `start` up to `end`, exclusive.
//
// We follow the Python implementation of slicing, since Python is
// the language of the meta-model specifications. Hence, the positions count
// the characters (code points), a negative position counts from the end,
// the positions out of range are clamped to the string, and the slice is empty
// if `start` is not before `end`.
func SliceStr(text string, start int64, end int64) string {{
{I}length := LenStr(text)
{I}theStart := resolvePosition(start, length)
{I}theEnd := resolvePosition(end, length)

{I}if theStart >= theEnd {{
{II}return ""
{I}}}

{I}return text[byteOffsetOf(text, theStart):byteOffsetOf(text, theEnd)]
}}"""
                ),
                Stripped(
                    f"""\
// Slice `text` from `start` up to its end.
//
// See [SliceStr] for the semantics.
func SliceStrFrom(text string, start int64) string {{
{I}theStart := resolvePosition(start, LenStr(text))
{I}return text[byteOffsetOf(text, theStart):]
}}"""
                ),
                Stripped(
                    f"""\
// Find the first `sub` in `text` from `start` on.
//
// Return the position of `sub` in `text`, or -1 if `sub` could not be found.
//
// We follow the Python implementation of `str.find`, since Python is
// the language of the meta-model specifications. Hence, the positions count
// the characters (code points), a negative `start` counts from the end, and
// a `start` beyond the end of `text` gives -1.
func FindStr(text string, sub string, start int64) int64 {{
{I}length := int64(LenStr(text))
{I}if start < 0 {{
{II}start += length
{II}if start < 0 {{
{III}start = 0
{II}}}
{I}}}

{I}if start > length {{
{II}return -1
{I}}}

{I}startOffset := byteOffsetOf(text, int(start))
{I}index := strings.Index(text[startOffset:], sub)
{I}if index == -1 {{
{II}return -1
{I}}}

{I}return start + int64(LenStr(text[startOffset:startOffset+index]))
}}"""
                ),
            ]
        )

    # NOTE (mristin):
    # We add the helpers only if the meta-model uses the respective operations so
    # that we do not clutter the code otherwise. The helpers live in the common
    # package so that both the verification and the methods in the types can use
    # them. They are exported so that the clients can rely on them, and so that we
    # can unit-test them.
    if intermediate_uses.modulo(symbol_table):
        blocks.append(FLOOR_MOD)

    if intermediate_uses.abs_call(symbol_table):
        blocks.append(ABS_INT64)

    if intermediate_uses.int_call(symbol_table):
        blocks.append(PARSE_SAFE_INT)

    if intermediate_uses.sets(symbol_table) or intermediate_uses.dicts(symbol_table):
        blocks.extend(SOME_AND_ALL_KEYS)

    if intermediate_uses.dicts(symbol_table):
        blocks.extend(MAP_LOOK_UPS)

    if intermediate_uses.set_operations(symbol_table):
        blocks.extend(SET_OPERATIONS)

    if intermediate_uses.set_properties(
        symbol_table
    ) or intermediate_uses.dict_properties(symbol_table):
        blocks.extend(SORTED_KEYS)

    blocks.append(golang_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
