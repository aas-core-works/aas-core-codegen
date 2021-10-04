"""Generate the visitor classes based on the intermediate representation."""

"""Generate the invariant verifiers from the intermediate representation."""
import io
import textwrap
import xml.sax.saxutils
from typing import Tuple, Optional, List, Union

from icontract import ensure, require

import aas_core_csharp_codegen.csharp.common as csharp_common
import aas_core_csharp_codegen.csharp.naming as csharp_naming
from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Error, Stripped, Rstripped, Identifier, \
    assert_never
from aas_core_csharp_codegen.csharp import specific_implementations
from aas_core_csharp_codegen.specific_implementations import ImplementationKey


# region Generate

def _generate_ivisitor(
        symbol_table: intermediate.SymbolTable
) -> Stripped:
    """Generate the most general visitor pattern."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.Interface):
            interface_name = csharp_naming.interface_name(symbol.name)
            var_name = csharp_naming.argument_name(symbol.name)
            blocks.append(Stripped(f'public T visit({interface_name} {var_name});'))

        elif isinstance(symbol, intermediate.Class):
            cls_name = csharp_naming.class_name(symbol.name)
            var_name = csharp_naming.argument_name(symbol.name)
            blocks.append(Stripped(f'public T visit({cls_name} {var_name});'))

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        textwrap.dedent('''\
            /// <summary>
            /// Define the interface for a visitor which visits the instances of the model.
            /// </summary>
            public interface IVisitor<T>
            {
                public T visit(IEntity entity);
            '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n')
        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write(f'\n}}  // public interface IVisitor')

    return Stripped(writer.getvalue())


def _generate_void_visitor(
        symbol_table: intermediate.SymbolTable
) -> Stripped:
    """Generate a visitor that does nothing and returns nothing."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.Interface):
            interface_name = csharp_naming.interface_name(symbol.name)
            var_name = csharp_naming.argument_name(symbol.name)
            blocks.append(Stripped(textwrap.dedent(f'''\
                public void visit({interface_name} {var_name})
                {{
                    // Dispatch
                    {var_name}.Accept(this);
                }}''')))

        elif isinstance(symbol, intermediate.Class):
            cls_name = csharp_naming.class_name(symbol.name)
            var_name = csharp_naming.argument_name(symbol.name)
            blocks.append(Stripped(textwrap.dedent(f'''\
                public void visit({cls_name} {var_name})
                {{
                    // Do nothing, but descend
                    foreach (var something in {var_name}.DescendOnce())
                    {{
                        something.Accept(this);
                    }}
                }}''')))

        else:
            assert_never(symbol)

    writer = io.StringIO()
    writer.write(
        textwrap.dedent('''\
            /// <summary>
            /// Provide a visitor that returns nothing and iterates over all the instances.
            /// </summary>
            /// <remarks>
            /// The visitor is based on the double-dispatch using <see cref="IEntity.Accept"> method.
            ///
            /// While meaningless on its own, extending this visitor is helpful if you only want 
            /// to implement a subset of visit methods, but still want to preserve deep iteration.
            /// </remarks> 
            public interface VoidVisitor : IVisitor<void>
            {
                public void visit(IEntity entity)
                {
                    // Dispatch
                    entity.Accept(this);
                }
            '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')
        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write(f'\n}}  // public class VoidVisitor')

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
        symbol_table: intermediate.SymbolTable,
        namespace: csharp_common.NamespaceIdentifier
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code of the visitors based on the intermediate representation

    The ``namespace`` defines the C# namespace.
    """
    blocks = [csharp_common.WARNING]  # type: List[Rstripped]

    writer = io.StringIO()
    writer.write(f"namespace {namespace}\n{{\n")
    writer.write(
        f"{csharp_common.INDENT}static class Visitation\n"
        f"{csharp_common.INDENT}{{\n")

    visitation_blocks = [
        _generate_ivisitor(symbol_table=symbol_table),
        _generate_void_visitor(symbol_table=symbol_table)
    ]

    for i, visitation_block in enumerate(visitation_blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(
            textwrap.indent(visitation_block, csharp_common.INDENT2))

    writer.write(
        f"\n{csharp_common.INDENT}}}  // static class Visitation")
    writer.write(f"\n}}  // namespace {namespace}")

    blocks.append(Stripped(writer.getvalue()))

    blocks.append(csharp_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write('\n\n')

        assert not block.startswith('\n')
        assert not block.endswith('\n')
        out.write(block)

    out.write('\n')

    return out.getvalue(), None

# endregion
