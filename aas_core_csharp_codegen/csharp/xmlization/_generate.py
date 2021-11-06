"""Generate C# code for XML-ization based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List, Sequence, MutableMapping

from icontract import ensure, require

from aas_core_csharp_codegen import intermediate, naming, specific_implementations
from aas_core_csharp_codegen.common import Error, Stripped, Identifier, \
    indent_but_first_line, assert_never
from aas_core_csharp_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming
)
# TODO: apply this trick to everything
from aas_core_csharp_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII
)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_serializer(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    errors = []  # type: List[Error]

    blocks = []  # type: List[Stripped]

    # TODO: continue here
    # TODO: consider inheriting from Visitor and accepting the XmlWriter
    # TODO: unroll collections and dictionaries 🠒 we need to know how to serialize those anyhow...
    # TODO: serialization of primitives: <Value>...</Value>
    # TODO: serialization of dictionaries: <Key>...</Key><Value>...</Value>

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        public class Serializer
        {{
        '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, I))

    writer.write('\n}  // public class Serializer')


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
        namespace: csharp_common.NamespaceIdentifier,
        interface_implementers: intermediate.InterfaceImplementers,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code for the general serialization.

    The ``namespace`` defines the AAS C# namespace.
    """
    errors = []  # type: List[Error]

    blocks = [
        csharp_common.WARNING,
        Stripped(textwrap.dedent(f"""\
            /*
             * We implement a streaming-based XML de/serialization with 
             * <see cref="System.Xml.XmlReader" /> and <see cref="System.Xml.XmlWriter" /> 
             * due to performance reasons.
             * For more information, see:
             * <ul>
             * <li>https://bertwagner.com/posts/xmlreader-vs-xmldocument-performance/</li>
             * <li>https://www.erikthecoder.net/2019/08/02/xml-parsing-performance-csharp-versus-go/</li>
             * <li>https://docs.microsoft.com/en-us/dotnet/standard/serialization/xml-serializer-generator-tool-sgen-exe</li>
             * </ul>
             */""")),
        Stripped(textwrap.dedent(f"""\
            using Xml = System.Xml;
            using System.Collections.Generic;  // can't alias

            using Aas = {namespace};"""))
    ]

    xmlization_blocks = []  # type: List[Stripped]

    serializer_code, serializer_errors = _generate_serializer(
        symbol_table=symbol_table,
        spec_impls=spec_impls
    )
    if serializer_errors is not None:
        errors.extend(serializer_errors)
    else:
        xmlization_blocks.append(serializer_code)

    # TODO: uncomment once implemented
    # deserializer_code, deserializer_errors = _generate_deserializer(
    #     symbol_table=symbol_table,
    #     interface_implementers=interface_implementers,
    #     spec_impls=spec_impls
    # )
    # if deserializer_errors is not None:
    #     errors.extend(deserializer_errors)
    # else:
    #     xmlization_blocks.append(serializer_code)

    if len(errors) > 0:
        return None, errors

    # TODO: move up
    for symbol in symbol_table.symbols:
        xmlization_block = None  # type: Optional[Stripped]
        if isinstance(symbol, intermediate.Enumeration):
            raise NotImplementedError()
        elif isinstance(symbol, intermediate.Interface):
            raise NotImplementedError()

        elif isinstance(symbol, intermediate.Class):
            raise NotImplementedError()
        else:
            assert_never(symbol)

        assert xmlization_block is not None
        xmlization_blocks.append(xmlization_block)

    writer = io.StringIO()
    # TODO: add better documentation!
    writer.write(textwrap.dedent(f'''\
        namespace {namespace}
        {{
        {I}public static class Xmlization
        {I}{{
        '''))

    for i, xmlization_block in enumerate(xmlization_blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(xmlization_block, II))

    writer.write(
        f"\n{I}}}  // public static class Xmlization")
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
