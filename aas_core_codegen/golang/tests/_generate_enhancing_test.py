"""Generate the test code for the enhancing of instances."""

import io

from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Stripped,
    Identifier,
)
from aas_core_codegen.golang import common as golang_common, naming as golang_naming
from aas_core_codegen.golang.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable, repo_url: Stripped) -> str:
    """Generate the test code for the enhancing of instances."""
    blocks = [
        Stripped("package enhancing_test"),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{I}"testing"
{I}aasenhancing "{repo_url}/enhancing"
{I}aastesting "{repo_url}/aastesting"
{I}aastypes "{repo_url}/types"
)"""
        ),
        Stripped(
            f"""\
type Enhancement struct {{
{I}ID int
}}"""
        ),
        Stripped(
            f"""\
func collectIDsAndAssertTheyAreConsecutiveAndTheirCountEqualsNextID(
{I}t *testing.T,
{I}wrapped aastypes.IClass,
{I}nextID int,
) {{
{I}var ids []int

{I}instanceEnh := aasenhancing.MustUnwrap[*Enhancement](wrapped)
{I}ids = append(ids, instanceEnh.ID)

{I}wrapped.Descend(
{II}func(that aastypes.IClass) (abort bool) {{
{III}enh := aasenhancing.MustUnwrap[*Enhancement](that)
{III}ids = append(ids, enh.ID)
{III}return
{II}}},
{I})

{I}if len(ids) != nextID {{
{II}t.Fatalf("Expected to collect %d IDs, but got: %d", len(ids), nextID)
{II}return
{I}}}

{I}for i, id := range ids {{
{II}if id != i {{
{III}t.Fatalf(
{IIII}"Unexpected ID at index %d (starting from 0); expected %d, got %d",
{IIII}i, i, id,
{III})
{II}}}
{I}}}
}}"""
        ),
    ]

    for concrete_cls in symbol_table.concrete_classes:
        must_load_maximal_name = golang_naming.function_name(
            Identifier(f"must_load_maximal_{concrete_cls.name}")
        )

        test_name = golang_naming.function_name(
            (Identifier(f"test_{concrete_cls.name}_wrapped"))
        )

        blocks.append(
            Stripped(
                f"""\
func {test_name}(t *testing.T) {{
{I}instance := aastesting.{must_load_maximal_name}()

{I}nextID := 0
{I}wrapped := aasenhancing.Wrap[*Enhancement](
{II}instance,
{II}func(that aastypes.IClass) (enh *Enhancement, should bool) {{
{III}enh = &Enhancement{{}}
{III}enh.ID = nextID
{III}should = true

{III}nextID++
{III}return
{II}}},
{I})

{I}if !aastesting.DeepEqual(instance, wrapped) {{
{II}t.Fatalf(
{III}"Deep equality failed between the instance and the wrapped: %v %v",
{III}instance, wrapped,
{II})
{I}}}

{I}collectIDsAndAssertTheyAreConsecutiveAndTheirCountEqualsNextID(
{II}t, wrapped, nextID,
{I})
}}"""
            )
        )

        test_name = golang_naming.function_name(
            (Identifier(f"test_{concrete_cls.name}_nothing_wrapped"))
        )

        blocks.append(
            Stripped(
                f"""\
func {test_name}(t *testing.T) {{
{I}instance := aastesting.{must_load_maximal_name}()

{I}wrapped := aasenhancing.Wrap[*Enhancement](
{II}instance,
{II}func(that aastypes.IClass) (enh *Enhancement, should bool) {{
{III}should = false
{III}return
{II}}},
{I})

{I}if !aastesting.DeepEqual(instance, wrapped) {{
{II}t.Fatalf(
{III}"Deep equality failed between the instance and the wrapped: %v %v",
{III}instance, wrapped,
{II})
{I}}}

{I}// Wrapped should be equal to instance by reference as our enhancement factory
{I}// did not wrap anything.
{I}if wrapped != instance {{
{II}t.Fatalf("Unexpected inequality between %v and %v", wrapped, instance)
{I}}}

{I}wrapped.Descend(func (that aastypes.IClass) (abort bool) {{
{II}_, ok := aasenhancing.Unwrap[*Enhancement](that)
{II}if ok {{
{III}t.Fatalf("Unexpected wrapped descendant: %v", that)
{II}}}
{II}return
{I}}})
}}"""
            )
        )

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
