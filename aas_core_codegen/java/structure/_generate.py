"""Generate the Java data structures from the intermediate representation."""
import io
from typing import (
    cast,
    List,
    Optional,
    Tuple,
)

from icontract import ensure, require

from aas_core_codegen import intermediate
from aas_core_codegen import specific_implementations
from aas_core_codegen.common import (
    Error,
    Stripped,
)
from aas_core_codegen.java import (
    common as java_common,
)
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
)

# region Checks


class VerifiedIntermediateSymbolTable(intermediate.SymbolTable):
    """Represent a verified symbol table which can be used for code generation."""

    # noinspection PyInitNewSignature
    def __new__(
        cls, symbol_table: intermediate.SymbolTable
    ) -> "VerifiedIntermediateSymbolTable":
        raise AssertionError("Only for type annotation")


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def verify(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[VerifiedIntermediateSymbolTable], Optional[List[Error]]]:
    """Verify that Java code can be generated from the ``symbol_table``."""

    return cast(VerifiedIntermediateSymbolTable, symbol_table), None


# endregion

# region Generation


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: VerifiedIntermediateSymbolTable,
    package: java_common.PackageIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the Java code of the structures based on the symbol table.

    The ``package`` defines the AAS Java package.
    """
    code_blocks = [
        Stripped(
            f"""\
/**
 * Represent a general class of an AAS model.
 */
public interface IClass
{{
{I}/**
{I} * Iterate over all the class instances referenced from this instance
{I} * without further recursion.
{I} */
{I}public Iterable<IClass> descendOnce();

{I}/**
{I} * Iterate recursively over all the class instances referenced from this instance.
{I} */
{I}public Iterable<IClass> descend();

{I}/**
{I} * Accept the {{@code visitor}} to visit this instance
{I} * for double dispatch.
{I} */
{I}public void accept(Visitation.IVisitor visitor);

{I}/**
{I} * Accept the visitor to visit this instance for double dispatch
{I} * with the {{@code context}}.
{I} */
{I}public <TContext> void accept(
{II}Visitation.IVisitorWithContext<TContext> visitor,
{II}TContext context);

{I}/**
{I} * Accept the {{@code transformer}} to transform this instance
{I} * for double dispatch.
{I} */
{I}public <T> T transform(Visitation.ITransformer<T> transformer);

{I}/**
{I} * Accept the {{@code transformer}} to visit this instance
{I} * for double dispatch with the {{@code context}}.
{I} */
{I}public <TContext, T> T transform(
{II}Visitation.ITransformerWithContext<TContext, T> transformer,
{II}TContext context);
}}"""
        )
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    if len(errors) > 0:
        return None, errors

    blocks = [
        java_common.WARNING,
        Stripped(
            f"""\
package {package};
// package {package}"""
        ),
        java_common.WARNING,
    ]  # type: List[Stripped]

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue(), None


# endregion
