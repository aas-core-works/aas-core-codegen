"""Generate the C# data structures from the intermediate representation."""
import io
import textwrap
from typing import Optional, Dict, List, Tuple, cast

import docutils.nodes
from icontract import ensure, require

import aas_core_csharp_codegen.csharp.common as csharp_common
from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen import specific_implementations
from aas_core_csharp_codegen.common import Error, Identifier, assert_never, \
    TRAILING_WHITESPACE_RE, Code
# region Checks
from aas_core_csharp_codegen.csharp import naming


def _verify_structure_name_collisions(
        intermediate_symbol_table: intermediate.SymbolTable
) -> List[Error]:
    """Verify that the C# names of the structures do not collide."""
    observed_structure_names = {}  # type: Dict[Identifier, intermediate.Symbol]

    errors = []  # type: List[Error]

    for symbol in intermediate_symbol_table.symbols:
        name = None  # type: Optional[Identifier]

        if isinstance(symbol, intermediate.Class):
            name = naming.class_name(symbol.name)
        elif isinstance(symbol, intermediate.Enumeration):
            name = naming.enum_name(symbol.name)
        elif isinstance(symbol, intermediate.Interface):
            name = naming.interface_name(symbol.name)
        else:
            assert_never(symbol)

        assert name is not None
        if name in observed_structure_names:
            # TODO: test
            errors.append(
                Error(
                    symbol.parsed.node,
                    f"The C# name {name!r} "
                    f"of the meta-model symbol {symbol.name!r} collides "
                    f"with another meta-model symbol "
                    f"{observed_structure_names[name].name!r}"))
        else:
            observed_structure_names[name] = symbol

    # region Intra-structure collisions

    for symbol in intermediate_symbol_table.symbols:
        collision_error = _verify_intra_structure_collisions(intermediate_symbol=symbol)

        if collision_error is not None:
            errors.append(collision_error)

    return errors


def _verify_intra_structure_collisions(
        intermediate_symbol: intermediate.Symbol
) -> Optional[Error]:
    """Verify that no member names collide in the C# structure of the given symbol."""
    errors = []  # type: List[Error]

    # TODO: revisit this method — it is outdated with the current implementation!

    # TODO: add method_name to _naming
    # TODO: include methods in this step

    if isinstance(intermediate_symbol, (intermediate.Class, intermediate.Interface)):
        observed_member_names = {}  # type: Dict[Identifier, str]

        for prop in intermediate_symbol.properties:
            private_prop_name = naming.private_property(prop.name)
            if private_prop_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C# private property {private_prop_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[private_prop_name]}"
                    ))
            else:
                observed_member_names[private_prop_name] = (
                    f"C# private property {private_prop_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}")

            getter_name = naming.getter_name(prop.name)
            if getter_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C# getter {getter_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[getter_name]}"
                    ))
            else:
                observed_member_names[getter_name] = (
                    f"C# getter {getter_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}")

            setter_name = naming.setter_name(prop.name)
            if setter_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C# setter {setter_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[setter_name]}"
                    ))
            else:
                observed_member_names[setter_name] = (
                    f"C# setter {setter_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}")

    elif isinstance(intermediate_symbol, intermediate.Enumeration):
        pass
    else:
        assert_never(intermediate_symbol)

    if len(errors) > 0:
        errors.append(
            Error(
                intermediate_symbol.parsed.node,
                f"Naming collision(s) in C# code "
                f"for the symbol {intermediate_symbol.name!r}",
                underlying=errors))

    return None


class VerifiedIntermediateSymbolTable(intermediate.SymbolTable):
    """Represent a verified symbol table which can be used for code generation."""

    def __new__(
            cls, intermediate_symbol_table: intermediate.SymbolTable
    ) -> 'VerifiedIntermediateSymbolTable':
        raise AssertionError("Only for type annotation")


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def verify(
        intermediate_symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[VerifiedIntermediateSymbolTable], Optional[List[Error]]]:
    """Verify that C# code can be generated from the ``intermediate_symbol_table``."""
    errors = []  # type: List[Error]

    structure_name_collisions = _verify_structure_name_collisions(
        intermediate_symbol_table=intermediate_symbol_table)

    errors.extend(structure_name_collisions)

    for symbol in intermediate_symbol_table.symbols:
        error = _verify_intra_structure_collisions(intermediate_symbol=symbol)
        if error is not None:
            errors.append(error)

    errors.extend(
        specific_implementations.verify_that_available_for_all_symbols(
            intermediate_symbol_table=intermediate_symbol_table,
            spec_impls=spec_impls))

    if len(errors) > 0:
        return None, errors

    return cast(VerifiedIntermediateSymbolTable, intermediate.SymbolTable), None


# endregion

# region Generation

class Block(str):
    """Represent a block of generated code."""

    @require(lambda code: not TRAILING_WHITESPACE_RE.match(code))
    def __new__(cls, block: str) -> 'Block':
        return cast(Block, block)


def _description_paragraph(
        paragraph: docutils.nodes.paragraph
) -> Tuple[Optional[Code], Optional[str]]:
    """
    Render the body of a description paragraph as documentation XML.

    :param paragraph: to be rendered
    :return: the generated code, or error if the paragraph could not be translated
    """
    # TODO: continue here

@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _description_comment(
        description: intermediate.Description
) -> Tuple[Optional[Code], Optional[Error]]:
    """Generate a documentation comment based on the docstring."""
    summary = None  # type: Optional[docutils.nodes.paragraph]
    remarks = None  # type: Optional[List[docutils.nodes.paragraph]]
    tail = []  # type: List[docutils.nodes.General]

    document = description.document

    # Try to match the summary and the remarks
    if (
            len(description.document.children) >= 2
            and isinstance(description.document.children[0], docutils.nodes.paragraph)
            and isinstance(description.document.children[1], docutils.nodes.paragraph)
    ):
        summary = description.document.children[0]

        remarks = [description.document.children[1]]
        last_remark_index = 1
        for child in description.document.children[2:]:
            if isinstance(child, docutils.nodes.paragraph):
                remarks.append(child)
                last_remark_index += 1

        tail = description.document.children[last_remark_index + 1:]
    elif (
            len(description.document.children) >= 1
            and isinstance(description.document.children[0], docutils.nodes.paragraph)
    ):
        summary = description.document.children[0]
        tail = description.document.children[1:]
    else:
        tail = description.document.children

    # TODO: implement once we know how to render a paragraph body



@require(lambda enum_symbol: not enum_symbol.is_implementation_specific)
def _generate_enum(enum_symbol: intermediate.Enumeration) -> Code:
    """Generate the C# code for the enum."""
    writer = io.StringIO()

    if enum_symbol.description is not None:
        writer.write(
            f"<summary>\n"
            f"{_description_comment(enum_symbol.description.strip())}\n"
            f"</summary>")
        writer.write("\n")

    name = naming.enum_name(enum_symbol.name)
    if len(enum_symbol.literals) == 0:
        writer.write(f"public enum {name}\n{{\n}}")
        return Code(writer.getvalue())

    writer.write(f"public enum {name}\n{{")
    for i, literal in enumerate(enum_symbol.literals):
        if i > 0:
            writer.write(",\n\n")

        writer.write(
            textwrap.indent(
                f'[EnumMember(Value = {csharp_common.string_literal(literal.value)})]\n'
                f'{naming.enum_literal_name(literal.name)}',
                csharp_common.INDENT))

    writer.write("\n}}")

    return Code(writer.getvalue())


@require(lambda enum_symbol: not enum_symbol.is_implementation_specific)
def _generate_interface(
        interface_symbol: intermediate.Interface,
        spec_impls: specific_implementations.SpecificImplementations
) -> Code:
    """Generate C# code for the given interface."""
    writer = io.StringIO()

    if interface_symbol.description is not None:
        writer.write(_description_comment(interface_symbol.description.strip()))
        writer.write("\n")

    name = naming.interface_name(interface_symbol.name)

    writer.write(f"public interface {name}\n{{\n")

    # Code blocks separated by double newlines and indented once
    codes = []  # type: List[Code]

    # region Getters and setters

    for prop in interface_symbol.properties:
        prop_type = csharp_common.generate_type(prop.type_annotation)
        prop_name = naming.property_name(prop.name)

        if prop.description is not None:
            prop_comment = _description_comment(prop.description.strip())
            codes.append(
                Code(f"{prop_comment}\n{prop_type} {prop_name} {{ get; set; }}"))
        else:
            codes.append(Code(f"{prop_type} {prop_type} {{ get; set; }}"))

    for signature in interface_symbol.signatures:
        description_blocks = []  # type: List[Block]
        if signature.description is not None:
            description_blocks.append(
                Block(f"<summary>\n{signature.description.strip()}\n</summary>"))

        if len(signature.arguments) > 0:
            argument_lines = []  # type: List[Block]
            for argument in signature.arguments:
                # TODO: continue here
                argument_description = argument.
                argument_lines.append(Block(
                    f'<param name="{naming.argument_name(argument.name)}">'
                ))

        # fmt: off
        returns = (
            csharp_common.generate_type(signature.returns)
            if signature.returns is not None else "void"
        )
        # fmt: on

        arg_codes = []  # type: List[Code]
        for arg in signature.arguments:
            arg_type = csharp_common.generate_type(arg.type_annotation)
            arg_name = naming.argument_name(arg.name)

        # TODO: write for methods

    # endregion

    # region Methods

    # endregion

    for i, code in enumerate(codes):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(code, csharp_common.INDENT))
    writer.write("\n\n".join(codes))
    writer.write("\n}}")

    return Code(writer.getvalue())


# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
        intermediate_symbol_table: VerifiedIntermediateSymbolTable,
        namespace: Identifier,
        spec_impls: specific_implementations.SpecificImplementations
) -> str:
    """
    Generate the C# code of the structures based on the symbol table.

    The ``namespace`` defines the C# namespace.
    """
    warning = Block(textwrap.dedent("""\
        /*
         * This code has been automatically generated by aas-core-csharp-codegen.
         * Do NOT edit or append.
         */"""))

    blocks = [warning]  # type: List[Block]

    using_directives = []  # type: List[str]
    if any(
            isinstance(symbol, intermediate.Enumeration)
            for symbol in intermediate_symbol_table.symbols
    ):
        using_directives.append(
            "using EnumMemberAttribute = "
            "System.Runtime.Serialization.EnumMemberAttribute;")

    if len(using_directives) > 0:
        blocks.append(Block("\n".join(using_directives)))

    blocks.append(Block(f"namespace {namespace}\n{{"))

    for intermediate_symbol in intermediate_symbol_table.symbols:
        code = None  # type: Optional[Code]

        if intermediate_symbol.is_implementation_specific:
            # TODO: test
            code = spec_impls[
                specific_implementations.ImplementationKey(
                    intermediate_symbol.name)]
        else:
            if isinstance(intermediate_symbol, intermediate.Enumeration):
                # TODO: test
                code = _generate_enum(enum_symbol=intermediate_symbol)
            elif isinstance(intermediate_symbol, intermediate.Interface):
                # TODO: test
                code = _generate_interface(
                    intermediate_symbol=intermediate_symbol,
                    spec_impls=spec_impls)
            elif isinstance(intermediate_symbol, intermediate.Class):
                # TODO: impl
                code = _generate_class(
                    intermediate_symbol=intermediate_symbol,
                    spec_impls=spec_impls)
            else:
                assert_never(intermediate_symbol)

        assert code is not None
        blocks.append(Block(textwrap.indent(code, '    ')))

    blocks.append(Block(f"}}  // namespace {namespace}"))

    blocks.append(warning)

    return '\n\n'.join(blocks)

# endregion

# TODO: implement live_test 🠒 use C# compiler to actually create and compile the code!
