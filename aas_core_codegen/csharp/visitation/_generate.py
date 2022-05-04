"""Generate the visitor classes based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List

from icontract import ensure

import aas_core_codegen.csharp.common as csharp_common
from aas_core_codegen.csharp.common import INDENT as I, INDENT2 as II
import aas_core_codegen.csharp.naming as csharp_naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Error, Stripped, Rstripped, assert_never


# region Generate


def _generate_ivisitor(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the visitor interface."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not visit them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not visit them.
            continue

        elif isinstance(symbol, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(Stripped(f"public void Visit({cls_name} that);"))

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Define the interface for a visitor which visits the instances of the model.
/// </summary>
public interface IVisitor
{{
{I}public void Visit(IClass that);
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public interface IVisitor")

    return Stripped(writer.getvalue())


def _generate_visitor_through(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the visitor that simply iterates over the instances."""
    blocks = [
        Stripped(
            f"""\
public void Visit(IClass that)
{{
{I}that.Accept(this);
}}"""
        )
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not visit them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not transform
            # them.
            continue

        elif isinstance(symbol, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(
                Stripped(
                    f"""\
public void Visit({cls_name} that)
{{
{I}// Just descend through, do nothing with <c>that</c>
{I}foreach (var something in that.DescendOnce())
{I}{{
{II}Visit(something);
{I}}}
}}"""
                )
            )

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        """\
/// <summary>
/// Just descend through the instances without any action.
/// </summary>
/// <remarks>
/// This class is meaningless for itself. However, it is a good base if you
/// want to descend through instances and apply actions only on a subset of
/// classes.
/// </remarks>
public class VisitorThrough : IVisitor
{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public class VisitorThrough")

    return Stripped(writer.getvalue())


def _generate_abstract_visitor(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the visitor that performs double-dispatch."""
    blocks = [
        Stripped(
            f"""\
public void Visit(IClass that)
{{
{I}that.Accept(this);
}}"""
        )
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not visit them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not transform
            # them.
            continue

        elif isinstance(symbol, intermediate.Class):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(Stripped(f"public abstract void Visit({cls_name} that);"))

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        """\
/// <summary>
/// Perform double-dispatch to visit the concrete instances.
/// </summary>
public abstract class AbstractVisitor : IVisitor
{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public abstract class AbstractVisitor")

    return Stripped(writer.getvalue())


def _generate_ivisitor_with_context(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the interface for the visitor with context."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not visit them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not visit them.
            continue

        elif isinstance(symbol, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(Stripped(f"public void Visit({cls_name} that, C context);"))

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Define the interface for a visitor which visits the instances of the model.
/// </summary>
/// <typeparam name="C">Context type</typeparam>
public interface IVisitorWithContext<C>
{{
{I}public void Visit(IClass that, C context);
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public interface IVisitorWithContext")

    return Stripped(writer.getvalue())


def _generate_abstract_visitor_with_context(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the visitor with context that performs double-dispatch."""
    blocks = [
        Stripped(
            f"""\
public void Visit(IClass that, C context)
{{
{I}that.Accept(this, context);
}}"""
        )
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not visit them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not transform
            # them.
            continue

        elif isinstance(symbol, intermediate.Class):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(
                Stripped(f"public abstract void Visit({cls_name} that, C context);")
            )

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Perform double-dispatch to visit the concrete instances
/// with context.
/// </summary>
/// <typeparam name="C">Context type</typeparam>
public abstract class AbstractVisitorWithContext<C>
{I}: IVisitorWithContext<C>
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public abstract class AbstractVisitorWithContext")

    return Stripped(writer.getvalue())


def _generate_itransformer(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the transformer interface."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not transform them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not transform
            # them.
            continue

        elif isinstance(symbol, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(Stripped(f"public T Transform({cls_name} that);"))

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Define the interface for a transformer which transforms recursively
/// the instances into something else.
/// </summary>
/// <typeparam name="T">The type of the transformation result</typeparam>
public interface ITransformer<T>
{{
{I}public T Transform(IClass that);
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public interface ITransformer")

    return Stripped(writer.getvalue())


def _generate_abstract_transformer(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the most abstract transformer that merely double-dispatches."""
    blocks = [
        Stripped(
            f"""\
public T Transform(IClass that)
{{
{I}return that.Transform(this);
}}"""
        )
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not transform them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not transform
            # them.
            continue

        elif isinstance(symbol, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(Stripped(f"public abstract T Transform({cls_name} that);"))

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        """\
/// <summary>
/// Perform double-dispatch to transform recursively
/// the instances into something else.
/// </summary>
/// <typeparam name="T">The type of the transformation result</typeparam>
public abstract class AbstractTransformer<T> : ITransformer<T>
{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public abstract class AbstractTransformer")

    return Stripped(writer.getvalue())


def _generate_itransformer_with_context(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the interface for the transformer with context."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not transform them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not transform
            # them.
            continue

        elif isinstance(symbol, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(Stripped(f"public T Transform({cls_name} that, C context);"))

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Define the interface for a transformer which recursively transforms
/// the instances into something else while the context is passed along.
/// </summary>
/// <typeparam name="C">Type of the transformation context</typeparam>
/// <typeparam name="T">The type of the transformation result</typeparam>
public interface ITransformerWithContext<C, T>
{{
{I}public T Transform(IClass that, C context);
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public interface ITransformerWithContext")

    return Stripped(writer.getvalue())


def _generate_abstract_transformer_with_context(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the most abstract transformer that merely double-dispatches."""
    blocks = [
        Stripped(
            f"""\
public T Transform(IClass that, C context)
{{
{I}return that.Transform(this, context);
}}"""
        )
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # Constrained primitives are modeled as their constrainees in C#,
            # so we do not transform them.
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # Abstract classes are modeled as interfaces in C#, so we do not transform
            # them.
            continue

        elif isinstance(symbol, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(symbol.name)
            blocks.append(
                Stripped(f"public abstract T Transform({cls_name} that, C context);")
            )

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Perform double-dispatch to transform recursively
/// the instances into something else.
/// </summary>
/// <typeparam name="C">The type of the transformation context</typeparam>
/// <typeparam name="T">The type of the transformation result</typeparam>
public abstract class AbstractTransformerWithContext<C, T>
{I}: ITransformerWithContext<C, T>
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public abstract class AbstractTransformerWithContext")

    return Stripped(writer.getvalue())


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable, namespace: csharp_common.NamespaceIdentifier
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code of the visitors based on the intermediate representation

    The ``namespace`` defines the AAS C# namespace.
    """
    blocks = [csharp_common.WARNING]  # type: List[Rstripped]

    writer = io.StringIO()
    writer.write(f"namespace {namespace}\n{{\n")
    writer.write(f"{I}public static class Visitation\n" f"{I}{{\n")

    visitation_blocks = [
        _generate_ivisitor(symbol_table=symbol_table),
        _generate_visitor_through(symbol_table=symbol_table),
        _generate_abstract_visitor(symbol_table=symbol_table),
        _generate_ivisitor_with_context(symbol_table=symbol_table),
        _generate_abstract_visitor_with_context(symbol_table=symbol_table),
        _generate_itransformer(symbol_table=symbol_table),
        _generate_abstract_transformer(symbol_table=symbol_table),
        _generate_itransformer_with_context(symbol_table=symbol_table),
        _generate_abstract_transformer_with_context(symbol_table=symbol_table),
    ]

    for i, visitation_block in enumerate(visitation_blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(visitation_block, II))

    writer.write(f"\n{I}}}  // public static class Visitation")
    writer.write(f"\n}}  // namespace {namespace}")

    blocks.append(Stripped(writer.getvalue()))

    blocks.append(csharp_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        assert not block.startswith("\n")
        assert not block.endswith("\n")
        out.write(block)

    out.write("\n")

    return out.getvalue(), None


# endregion
