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


def _generate_enum_value_sets(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate a class that pre-computes the sets of allowed enumeration literals."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.Enumeration):
            continue

        enum_name = csharp_naming.enum_name(symbol.name)
        blocks.append(Stripped(
            f"public static HashSet<int> For{enum_name} = "
            f"System.Enum.GetValues({enum_name});"))

    writer = io.StringIO()
    writer.write(textwrap.dedent('''\
        /// <summary>
        /// Hash allowed enum values to allow for efficient validation of enums.
        /// </summary> 
        private static class EnumValueSet
        {
        '''))
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n')

        writer.write(textwrap.indent(block, csharp_common.INDENT))

    return Stripped(writer.getvalue())


def _type_annotation_involves_enumeration(
        type_annotation: intermediate.TypeAnnotation
) -> bool:
    """
    Check whether the type annotation involves an enumeration.
    
    ``type_annotation`` can refer to an enumeration itself, but an enumeration can
    also be contained in it (*e.g.*, as keys in a mapping).
    """
    if isinstance(type_annotation, intermediate.BuiltinAtomicTypeAnnotation):
        return False
    elif isinstance(type_annotation, intermediate.OurAtomicTypeAnnotation):
        return isinstance(type_annotation.symbol, intermediate.Enumeration)
    elif isinstance(type_annotation, (
            intermediate.ListTypeAnnotation,
            intermediate.SequenceTypeAnnotation,
            intermediate.SetTypeAnnotation
    )):
        return _type_annotation_involves_enumeration(type_annotation.items)
    elif isinstance(type_annotation, (
            intermediate.MappingTypeAnnotation,
            intermediate.MutableMappingTypeAnnotation
    )):
        return (
                _type_annotation_involves_enumeration(type_annotation.keys)
                or _type_annotation_involves_enumeration(type_annotation.values)
        )
    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        return _type_annotation_involves_enumeration(type_annotation.value)
    else:
        assert_never(type_annotation)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_implementation_verify(cls: intermediate.Class) -> Stripped:
    """Generate the verify function in the ``Implementation`` class."""
    blocks = []  # type: List[Stripped]

    # TODO: transpile the invariants into body_blocks

    # for prop in cls.properties:
    #
    #
    # TODO: check that all enumerations are in the valid range!
    # TODO: this means, we need to unroll the subscripted types:
    # TODO: if the current type is an enumeration 🠒 check it
    # TODO: if the current type is a collection 🠒 unroll
    # TODO: if the current type is a mapping/mutable mapping 🠒 if keys() 🠒 unroll, if values 🠒 unroll

    if len(blocks) == 0:
        return Stripped("")

    cls_name = csharp_naming.class_name(cls.name)
    arg_name = csharp_naming.argument_name(cls.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        /// <summary>
        /// Verify the given <paramref name={xml.sax.saxutils.quoteattr(arg_name)} /> and 
        /// append any errors to <paramref name="Errors" />.
        /// </summary>
        public void Verify{cls_name} (
        {csharp_common.INDENT}{cls_name} {arg_name},
        {csharp_common.INDENT}Errors errors)
        {{
        '''))
    # TODO: finish

@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_implementation(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate a private static class, ``Implementation``, with verification logic."""
    errors = []  # type: List[Error]
    blocks = [
        _generate_enum_value_sets(symbol_table=symbol_table)
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, (intermediate.Enumeration, intermediate.Interface)):
            continue

        if symbol.implementation_key is not None:
            visit_key = ImplementationKey(
                f'Verification/Implementation/verify_{symbol.name}')
            if visit_key not in spec_impls:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"The implementation snippet is missing for "
                        f"the ``Verify`` method: {visit_key}"))
                continue

            blocks.append(spec_impls[visit_key])
        else:
            verify, error = _generate_implementation_verify(cls=symbol)

            if error is not None:
                errors.append(error)
                continue

            blocks.append(verify)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
            /// <summary>
            /// Verify the instances of the model entities non-recursively.
            /// </summary>
            /// <remarks>
            /// The methods provided by this class are re-used in the verification
            /// visitors.
            /// </remarks>
            private static class Implementation
            {{
            '''))
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}  // private static class Implementation')

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_verifier(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the ``Verifier`` class which visits the entities and verifies them."""
    # TODO: rewrite this

    blocks = [
        Stripped("public readonly Errors Errors;"),
        Stripped(textwrap.dedent(f'''\
            /// <summary>
            /// Initialize the visitor with the given <paramref name="errors" />.
            ///
            /// The errors observed during the visitation will be appended to
            /// the <paramref name="errors" />.
            /// </summary>
            Verifier(Errors errors)
            {{
            {csharp_common.INDENT}_errors = errors;
            }}
            ''')),
        Stripped(textwrap.dedent(f'''\
            public void Visit(IEntity entity)
            {{
            {csharp_common.INDENT}entity.Accept(this);
            }}'''))
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        /// <summary>
        /// Verify the instances of the model entities non-recursively.
        /// </summary>
        public static class NonRecursiveVerifier
        {{
        '''))
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}  // public static class NonRecursively')

    return Stripped(writer.getvalue()), None


# TODO: remove below
# def _generate_verify_class(
#         cls: intermediate.Class,
#         spec_impls: specific_implementations.SpecificImplementations
# ) -> Tuple[Optional[Stripped], Optional[Error]]:
#     """Generate the verify function for the given class."""
#     # If a class is implementation-specific, check if there is a special verification
#     # for it.
#     if cls.implementation_key is not None:
#         verification_implementation_key = f"Verification/{cls.name}"
#         code = spec_impls.get(verification_implementation_key, None)
#         if code is not None:
#             return code, None
#
#     writer = io.StringIO()
#
#     verify_blocks = []  # type: List[str]
#
#     if len(cls.invariants) == 0:
#         verify_blocks.append(
#             f"// There were no invariants specified "
#             f"for {csharp_naming.class_name(cls.name)}.\n"
#             f"return;")
#     else:
#         verify_blocks.append("if (errors.Full()) return;")
#         # TODO: transpile the invariants into body_blocks
#
#         # TODO: check that all enumerations are in the valid range!
#         pass
#
#     cls_name = csharp_naming.class_name(cls.name)
#     verify_name = Identifier(f"Verify{cls_name}")
#     arg_name = Identifier(csharp_naming.argument_name(cls.name))
#
#     writer.write(
#         textwrap.dedent(f'''\
#             /// <summary>
#             /// Verify <see cref={xml.sax.saxutils.quoteattr(cls_name)} />.
#             /// </summary>
#             /// <remarks>
#             /// Do not recurse to verify the children entities.
#             /// </remarks>
#             public void {verify_name}(
#                 {cls_name} {arg_name},
#                 Errors errors)
#             {{
#             '''))
#
#     writer.write(
#         textwrap.indent(
#             Stripped('\n\n'.join(verify_blocks)), csharp_common.INDENT))
#
#     writer.write("\n}\n\n")
#
#     verify_recursively_blocks = [
#         f"{verify_name}(errors);\n"
#         "if (errors.Full()) return;"
#     ]  # type: List[str]
#
#     for prop in cls.properties:
#         if isinstance(prop.type_annotation, intermediate.BuiltinAtomicTypeAnnotation):
#             continue
#         elif isinstance(prop.type_annotation, intermediate.OurAtomicTypeAnnotation):
#             prop_symbol = prop.type_annotation.symbol
#
#             if isinstance(prop_symbol, intermediate.Enumeration):
#                 continue
#             elif isinstance(prop_symbol, intermediate.Class):
#                 prop_cls_name = csharp_naming.class_name(prop_symbol.name)
#                 prop_name = csharp_naming.property_name(prop.name)
#
#                 verify_recursively_blocks.append(
#                     textwrap.dedent(f'''\
#                         VerifyRecursively{prop_cls_name}(
#                         {csharp_common.INDENT}{arg_name}.{prop_name},
#                         {csharp_common.INDENT}errors);
#                         if (errors.Full()) return;'''))
#
#             elif isinstance(prop_symbol, intermediate.Interface):
#                 prop_interface_name = csharp_naming.interface_name(prop_symbol.name)
#                 prop_name = csharp_naming.property_name(prop.name)
#
#                 verify_recursively_blocks.append(
#                     textwrap.dedent(f'''\
#                         VerifyRecursively{prop_interface_name}(
#                         {csharp_common.INDENT}{arg_name}.{prop_name},
#                         {csharp_common.INDENT}errors);
#                         if (errors.Full()) return;'''))
#             else:
#                 assert_never(prop_symbol)
#
#         elif isinstance(prop.type_annotation, intermediate.SubscriptedTypeAnnotation):
#             verify_recursively_blocks.append(
#                 _generate_unrolling_for_recursive_verify(cls=cls, prop=prop))
#
#         elif isinstance(prop.type_annotation, intermediate.SelfTypeAnnotation):
#             raise AssertionError(
#                 f"Unexpected self type annotation for a property {prop.name!r} "
#                 f"of class {cls.name}")
#         else:
#             assert_never(prop.type_annotation)
#
#     writer.write(
#         textwrap.dedent(f'''\
#             /// <summary>
#             /// Verify <see cref={xml.sax.saxutils.quoteattr(cls_name)} /> and
#             /// recurse into the contained children entities.
#             /// </summary>
#             public void VerifyRecursively{cls_name}(
#                 {cls_name} {arg_name},
#                 Errors errors)
#             {{
#             '''))
#
#     writer.write(
#         textwrap.indent(
#             Stripped('\n\n'.join(verify_recursively_blocks)), csharp_common.INDENT))
#
#     writer.write("\n}")
#
#     return Stripped(writer.getvalue()), None
#
#
# def _generate_verify_interface(
#         interface: intermediate.Interface,
#         interface_implementers: intermediate.InterfaceImplementers
# ) -> Tuple[Optional[Stripped], Optional[Error]]:
#     """Generate the verify function for the given interface."""
#     implementers = interface_implementers.get(interface, [])
#
#     interface_name = csharp_naming.interface_name(interface.name)
#     arg_name = csharp_naming.argument_name(interface.name)
#
#     if len(implementers) == 0:
#         code = textwrap.dedent(f'''\
#             public void Verify{interface_name}(
#             {csharp_common.INDENT}{interface_name} {arg_name},
#             {csharp_common.INDENT}Errors errors)
#             {{
#             {csharp_common.INDENT}// There are no implementer classes for this interface,
#             {csharp_common.INDENT}// so there is no verification function to dispatch to.
#             {csharp_common.INDENT}return;
#             }}
#
#             public void VerifyRecursively{interface_name}(
#             {csharp_common.INDENT}{interface_name} {arg_name},
#             {csharp_common.INDENT}Errors errors)
#             {{
#             {csharp_common.INDENT}// There are no implementer classes for this interface,
#             {csharp_common.INDENT}// so there is no verification function to dispatch to.
#             {csharp_common.INDENT}return;
#             }}''')
#
#         return Stripped(code), None
#
#     @require(lambda function_prefix: function_prefix in ('Verify', 'VerifyRecursively'))
#     def generate_dispatch(function_prefix: str) -> Stripped:
#         """Generate the dispatch function with the ``function_prefix``."""
#         blocks = [
#             "if (errors.Full()) return;"
#         ]  # type: List[str]
#
#         switch_writer = io.StringIO()
#         switch_writer.write(f"switch ({arg_name})\n{{\n")
#
#         for implementer in implementers:
#             cls_name = csharp_naming.class_name(implementer.name)
#             var_name = csharp_naming.variable_name(implementer.name)
#
#             switch_writer.write(
#                 textwrap.indent(
#                     textwrap.dedent(f'''\
#                         case {cls_name} {var_name}:
#                         {csharp_common.INDENT}{function_prefix}{cls_name}(
#                         {csharp_common.INDENT2}{var_name}, errors);
#                         {csharp_common.INDENT}break;
#                         '''),
#                     csharp_common.INDENT))
#
#         switch_writer.write(
#             textwrap.indent(
#                 textwrap.dedent(f'''\
#                     default:
#                     {csharp_common.INDENT}throw new InvalidArgumentException(
#                     {csharp_common.INDENT2}$"Unexpected implementing class of "
#                     {csharp_common.INDENT2}$"{{nameof({interface_name})}}: {{{arg_name}.GetType()}}");
#                     {csharp_common.INDENT}break;
#                     '''),
#                 csharp_common.INDENT))
#
#         switch_writer.write("}")
#         blocks.append(switch_writer.getvalue())
#
#         switch_writer = io.StringIO()
#         switch_writer.write(
#             textwrap.dedent(f'''\
#                 public void {function_prefix}{interface_name}(
#                 {csharp_common.INDENT}{interface_name} {arg_name},
#                 {csharp_common.INDENT}Errors errors)
#                 {{
#                 '''))
#
#         for i, block in enumerate(blocks):
#             if i > 0:
#                 switch_writer.write("\n\n")
#             switch_writer.write(textwrap.indent(block, csharp_common.INDENT))
#
#         switch_writer.write("\n}")
#
#         return Stripped(switch_writer.getvalue())
#
#     writer = io.StringIO()
#
#     verify_dispatch = generate_dispatch(function_prefix="Verify")
#     verify_recursively_dispatch = generate_dispatch(function_prefix="VerifyRecursively")
#
#     writer.write(
#         textwrap.dedent(f'''\
#             /// <summary>
#             /// Dispatch dynamically to the corresponding concrete verifier of
#             /// the underlying implementing class of {interface_name}.
#             /// </summary>
#             '''))
#     writer.write(generate_dispatch(function_prefix="Verify"))
#     writer.write('\n\n')
#
#     writer.write(
#         textwrap.dedent(f'''\
#             /// <summary>
#             /// Dispatch dynamically to the corresponding concrete recursive verifier of
#             /// the underlying implementing class of {interface_name}.
#             /// </summary>
#             '''))
#     writer.write(generate_dispatch(function_prefix="VerifyRecursively"))
#
#     return Stripped(writer.getvalue()), None


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
    blocks = [csharp_common.WARNING]  # type: List[Rstripped]

    using_directives = [
        "using ArgumentException = System.ArgumentException;\n"
        "using Regex = System.Text.RegularExpressions.Regex;\n"
        "using System.Collections.Generic;  // can't alias"
        "using System.Linq;  // can't alias"
    ]  # type: List[str]

    blocks.append(Stripped("\n".join(using_directives)))

    verification_blocks = [
        _generate_pattern_class(spec_impls=spec_impls),
        spec_impls[ImplementationKey('Verification/Error')],
        spec_impls[ImplementationKey('Verification/Errors')]
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    implementation, implementation_errors = _generate_implementation(
        symbol_table=symbol_table, spec_impls=spec_impls)
    if implementation_errors:
        errors.extend(implementation_errors)
    else:
        verification_blocks.append(implementation)

    verifier, error = _generate_verifier(
        symbol_table=symbol_table,
        spec_impls=spec_impls)

    # TODO: implement _generate_recursive_verifier

    if error is not None:
        errors.append(error)
    else:
        verification_blocks.append(verifier)

    if len(errors) > 0:
        return None, errors

    verification_writer = io.StringIO()
    verification_writer.write(f"namespace {namespace}\n{{\n")
    verification_writer.write(
        f"{csharp_common.INDENT}public static class Verification\n"
        f"{csharp_common.INDENT}{{\n")

    for i, verification_block in enumerate(verification_blocks):
        if i > 0:
            verification_writer.write('\n\n')

        verification_writer.write(
            textwrap.indent(verification_block, 2 * csharp_common.INDENT))

    verification_writer.write(
        f"\n{csharp_common.INDENT}}}  // public static class Verification")
    verification_writer.write(f"\n}}  // namespace {namespace}")

    blocks.append(Stripped(verification_writer.getvalue()))

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
