"""Generate the invariant verifiers from the intermediate representation."""
import io
import textwrap
import xml.sax.saxutils
from typing import Tuple, Optional, List, Union

from icontract import ensure

import aas_core_csharp_codegen.csharp.common as csharp_common
import aas_core_csharp_codegen.csharp.naming as csharp_naming
from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Error, Stripped, Rstripped, Identifier, \
    assert_never
from aas_core_csharp_codegen.csharp import specific_implementations
from aas_core_csharp_codegen.specific_implementations import ImplementationKey


# region Verify

def verify(
        spec_impls: specific_implementations.SpecificImplementations
) -> Optional[List[str]]:
    """Verify all the implementation snippets related to verification."""
    errors = []  # type: List[str]

    expected_keys = [
        'Verification/is_IRI', 'Verification/is_IRDI', 'Verification/is_ID_short',
        'Verification/Error', 'Verification/Errors'
    ]
    for key in expected_keys:
        if ImplementationKey(key) not in spec_impls:
            errors.append(f"The implementation snippet is missing for: {key}")

    if len(errors) == 0:
        return None

    return errors


# endregion

# region Generate

def _generate_pattern_class(
        spec_impls: specific_implementations.SpecificImplementations
) -> Stripped:
    """Generate the Pattern class used for verifying different patterns."""
    blocks = [
        spec_impls[ImplementationKey('Verification/is_IRI')],
        spec_impls[ImplementationKey('Verification/is_IRDI')],
        spec_impls[ImplementationKey('Verification/is_ID_short')]
    ]  # type: List[str]

    writer = io.StringIO()
    writer.write('public static class Pattern\n{\n')
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block.strip(), csharp_common.INDENT))

    writer.write('\n}')
    return Stripped(writer.getvalue())


def _generate_verify_class(
        cls: intermediate.Class,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the verify function for the given class."""
    # If a class is implementation-specific, check if there is a special verification
    # for it.
    if cls.implementation_key is not None:
        verification_implementation_key = f"Verification/{cls.name}"
        code = spec_impls.get(verification_implementation_key, None)
        if code is not None:
            return code, None

    writer = io.StringIO()

    verify_blocks = []  # type: List[str]

    if len(cls.invariants) == 0:
        verify_blocks.append(
            f"// There were no invariants specified "
            f"for {csharp_naming.class_name(cls.name)}.\n"
            f"return;")
    else:
        verify_blocks.append("if (errors.Full()) return;")
        # TODO: transpile the invariants into body_blocks
        pass

    cls_name = csharp_naming.class_name(cls.name)
    verify_name = Identifier(f"Verify{cls_name}")
    arg_name = Identifier(csharp_naming.argument_name(cls.name))

    writer.write(
        textwrap.dedent(f'''\
            /// <summary>
            /// Verify <see cref={xml.sax.saxutils.quoteattr(cls_name)} />.
            /// </summary>
            /// <remarks>
            /// Do not recurse to verify the children entities.
            /// </remarks>
            public void {verify_name}(
                {cls_name} {arg_name},
                Errors errors)
            {{
            '''))

    writer.write(
        textwrap.indent(
            Stripped('\n\n'.join(verify_blocks)), csharp_common.INDENT))

    writer.write("\n}\n\n")

    verify_recursively_blocks = [
        "if (errors.Full()) return;",
        f"{verify_name}(errors);"
    ]  # type: List[str]

    # TODO: generate VerifyRecursively{cls}
    #  🠒 unroll containers manually. This is a pain, but we lack the template specialization in C#.
    #  🠒 See: https://stackoverflow.com/questions/600978/how-to-do-template-specialization-in-c-sharp

    verify_recursively_name = Identifier(
        f"VerifyRecursively{csharp_naming.class_name(cls.name)}")

    writer.write(
        textwrap.dedent(f'''\
            /// <summary>
            /// Verify <see cref={xml.sax.saxutils.quoteattr(cls_name)} /> and recurse into the contained children entities.
            /// </summary>
            public void VerifyRecursively{cls_name}(
                {cls_name} {arg_name},
                Errors errors)
            {{
            '''))

    writer.write(
        textwrap.indent(
            Stripped('\n\n'.join(verify_recursively_blocks)), csharp_common.INDENT))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_verify_interface(
        interface: intermediate.Interface,
        interface_implementers: intermediate.InterfaceImplementers
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the verify function for the given interface."""
    implementers = interface_implementers[interface]

    interface_name = csharp_naming.interface_name(interface.name)
    arg_name = csharp_naming.argument_name(interface.name)

    if len(implementers) == 0:
        code = textwrap.dedent(f'''\
            public void Verify{interface_name}(
            {csharp_common.INDENT}{interface_name} {arg_name},
            {csharp_common.INDENT}Errors errors)
            {{
            {csharp_common.INDENT}// There are no implementer classes for this interface,
            {csharp_common.INDENT}// so there is no verification function to dispatch to.
            {csharp_common.INDENT}return;
            }}

            public void VerifyRecursively{interface_name}(
            {csharp_common.INDENT}{interface_name} {arg_name},
            {csharp_common.INDENT}Errors errors)
            {{
            {csharp_common.INDENT}// There are no implementer classes for this interface,
            {csharp_common.INDENT}// so there is no verification function to dispatch to.
            {csharp_common.INDENT}return;
            }}''')

        return Stripped(code), None

    # region Verify

    verify_blocks = [
        "if (errors.Full()) return;"
    ]  # type: List[str]

    writer = io.StringIO()
    writer.write(f"switch ({arg_name})\n{{\n")

    for implementer in implementers:
        cls_name = csharp_naming.class_name(implementer.name)
        var_name = csharp_naming.variable_name(implementer.name)

        writer.write(
            textwrap.dedent(f'''\
                {csharp_common.INDENT}case {cls_name} {var_name}:
                {csharp_common.INDENT2}Verify{cls_name}(
                {csharp_common.INDENT3}{var_name}, errors);
                {csharp_common.INDENT2}break;'''))

    writer.write(
        textwrap.dedent(f'''\
            {csharp_common.INDENT}default:
            {csharp_common.INDENT2}throw new InvalidArgumentError(
            {csharp_common.INDENT3}$"Unexpected implementing class of" 
            {csharp_common.INDENT3}$"{{nameof({interface_name})}}: {{{arg_name}.GetType()}}");
            {csharp_common.INDENT2}break;'''))

    writer.write("}")
    verify_blocks.append(writer.getvalue())

    # endregion

    # TODO: VerifyRecursively{interface name} 🠒 dispatch to the corresponding class, use must_find_interface_descendants



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
        spec_impls: specific_implementations.SpecificImplementations,
        interface_implementers: intermediate.InterfaceImplementers
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code of the structures based on the symbol table.

    The ``namespace`` defines the C# namespace.
    """
    warning = Stripped(textwrap.dedent("""\
        /*
         * This code has been automatically generated by aas-core-csharp-codegen.
         * Do NOT edit or append.
         */"""))

    blocks = [warning]  # type: List[Rstripped]

    using_directives = [
        "using ArgumentException = System.ArgumentException;\n"
        "using Regex = System.Text.RegularExpressions.Regex;\n"
        "using System.Collections.Generic;  // can't alias"
    ]  # type: List[str]

    blocks.append(Stripped("\n".join(using_directives)))

    verification_blocks = [
        _generate_pattern_class(spec_impls=spec_impls),
        spec_impls[ImplementationKey('Verification/Error')],
        spec_impls[ImplementationKey('Verification/Errors')]
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        error = None  # type: Optional[Error]
        verify_block = None  # type: Optional[Stripped]

        if isinstance(symbol, intermediate.Enumeration):
            continue
        elif isinstance(symbol, intermediate.Class):
            verify_block, error = _generate_verify_class(
                cls=symbol, spec_impls=spec_impls)
        elif isinstance(symbol, intermediate.Interface):
            verify_block, error = _generate_verify_interface(
                interface=symbol,
                interface_implementers=interface_implementers)
        else:
            assert_never(symbol)

        if error is not None:
            errors.append(error)
            continue

        verification_blocks.append(verify_block)

    if len(errors) > 0:
        return None, errors

    verification_writer = io.StringIO()
    verification_writer.write(f"namespace {namespace}\n{{\n")
    verification_writer.write(
        f"{csharp_common.INDENT}static class Verification\n"
        f"{csharp_common.INDENT}{{\n")

    for i, verification_block in enumerate(verification_blocks):
        if i > 0:
            verification_writer.write('\n\n')

        verification_writer.write(
            textwrap.indent(verification_block, 2 * csharp_common.INDENT))

    verification_writer.write(f"\n{csharp_common.INDENT}}}  // class Verification")
    verification_writer.write(f"\n}}  // namespace {namespace}")

    blocks.append(Stripped(verification_writer.getvalue()))

    blocks.append(warning)

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
