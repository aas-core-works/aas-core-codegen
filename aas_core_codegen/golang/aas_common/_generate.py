"""Generate Golang code of common functions by including the code directly."""

import io

from icontract import ensure

from aas_core_codegen.common import (
    Stripped,
)
from aas_core_codegen.golang import (
    common as golang_common,
)
from aas_core_codegen.golang.common import INDENT as I, INDENT2 as II, INDENT3 as III


# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate() -> str:
    """Generate the Golang code for common functions."""
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
{I}"strings"
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
func SomeRange(condition func(int) bool, start int, end int) bool {{
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
func AllRange(condition func(int) bool, start int, end int) bool {{
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
// Create a new instance of the `value` and return the pointer to it.
func NewBool(value bool) *bool {{
{I}return &value
}}"""
        ),
        Stripped(
            f"""\
// Create a new instance of the `value` and return the pointer to it.
func NewInt(value int) *int {{
{I}return &value
}}"""
        ),
        Stripped(
            f"""\
// Create a new instance of the `value` and return the pointer to it.
func NewInt64(value int64) *int64 {{
{I}return &value
}}"""
        ),
        Stripped(
            f"""\
// Create a new instance of the `value` and return the pointer to it.
func NewFloat64(value float64) *float64 {{
{I}return &value
}}"""
        ),
        Stripped(
            f"""\
// Create a new instance of the `value` and return the pointer to it.
func NewString(value string) *string {{
{I}return &value
}}"""
        ),
        golang_common.WARNING,
    ]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()
