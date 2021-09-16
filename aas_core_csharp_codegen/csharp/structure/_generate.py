"""Generate the C# data structures from the intermediate representation."""
import io
import textwrap
import xml.sax.saxutils
from typing import Optional, Dict, List, Tuple, cast

import docutils.nodes
from icontract import ensure, require

import aas_core_csharp_codegen.csharp.common as csharp_common
from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen import specific_implementations
from aas_core_csharp_codegen.common import Error, Identifier, assert_never, \
    Stripped
from aas_core_csharp_codegen.csharp import naming


# region Checks

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

    if isinstance(intermediate_symbol, (intermediate.Class, intermediate.Interface)):
        observed_member_names = {}  # type: Dict[Identifier, str]

        for prop in intermediate_symbol.properties:
            prop_name = naming.property_name(prop.name)
            if prop_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C# property {prop_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[prop_name]}"
                    ))
            else:
                observed_member_names[prop_name] = (
                    f"C# property {prop_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}")

        for method in intermediate_symbol.methods:
            method_name = naming.method_name(method.name)

            if method_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        method.parsed.node,
                        f"C# method {method_name!r} corresponding "
                        f"to the meta-model method {method.name!r} collides with "
                        f"the {observed_member_names[method_name]}"
                    ))
            else:
                observed_member_names[method_name] = (
                    f"C# method {method_name!r} corresponding to "
                    f"the meta-model method {method.name!r}")

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

def _description_paragraph_as_text(
        paragraph: docutils.nodes.paragraph
) -> Tuple[Optional[Stripped], Optional[str]]:
    """
    Render the body of a description paragraph as documentation XML.

    :param paragraph: to be rendered
    :return: the generated code, or error if the paragraph could not be translated
    """
    # TODO: test
    if len(paragraph.children) != 1:
        return (
            None,
            f"Expected a paragraph of a docstring to have a single child "
            f"(a docutils text), but got: {paragraph}")

    # TODO: test
    if not isinstance(paragraph.children[0], docutils.nodes.Text):
        return (
            None,
            f"Expected a paragraph of a docstring to consist only of text, "
            f"but got: {paragraph}")

    return paragraph.children[0].astext(), None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _description_comment(
        description: intermediate.Description
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate a documentation comment based on the docstring."""
    if len(description.document.children) == 0:
        return Stripped(""), None

    summary = None  # type: Optional[docutils.nodes.paragraph]
    remarks = None  # type: Optional[List[docutils.nodes.paragraph]]
    tail = []  # type: List[docutils.nodes.General]

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

    # (2021-09-16, mristin)
    # We restrict ourselves here quite a lot. This function will need to evolve as
    # we add a larger variety of docstrings to the meta-model.
    #
    # For example, we need to translate ``:paramref:``'s to ``<paramref ...>`` in C#.
    # Additionally, we need to change the name of the argument accordingly (snake_case
    # to camelCase).

    # Blocks to be joined by a new-line
    blocks = []  # type: List[Stripped]

    if summary:
        summary_text, error = _description_paragraph_as_text(summary)
        if error:
            return None, Error(description.node, error)

        blocks.append(
            Stripped(
                f'<summary>\n'
                f'{xml.sax.saxutils.escape(summary_text)}\n'
                f'</summary>'))

    if remarks:
        remark_blocks = []  # type: List[Stripped]
        for remark in remarks:
            remark_text, error = _description_paragraph_as_text(remark)
            if error:
                return None, Error(description.node, error)

            remark_blocks.append(remark_text)

        assert len(remark_blocks) >= 1, \
            f"Expected at least one remark block since ``remarks`` defined: {remarks}"

        if len(remark_blocks) == 1:
            blocks.append(
                Stripped(
                    f'<remarks>\n'
                    f'{xml.sax.saxutils.escape(remark_blocks[0])}\n'
                    f'</remarks>'))
        else:
            remarks_paras = '\n'.join(
                f'<para>{xml.sax.saxutils.escape(remark_block)}</para>'
                for remark_block in remark_blocks)

            blocks.append(
                Stripped(
                    f'<remarks>\n'
                    f'{remarks_paras}\n'
                    f'</remarks>'))

    for tail_element in tail:
        # TODO: test
        if not isinstance(tail_element, docutils.nodes.field_list):
            return (
                None,
                Error(
                    description.node,
                    f"Expected only a field list to follow the summary and remarks, "
                    f"but got: {tail_element}"))

        for field in tail_element.children:
            assert len(field.children) == 2
            field_name, field_body = field.children
            assert isinstance(field_name, docutils.nodes.field_name)
            assert isinstance(field_body, docutils.nodes.field_body)

            # region Generate field body

            body_blocks = []  # type: List[Stripped]
            for body_child in field_body.children:
                if isinstance(body_child, docutils.nodes.paragraph):
                    body_block, error = _description_paragraph_as_text(body_child)
                    if error:
                        return None, Error(description.node, error)

                    body_blocks.append(body_block)
                else:
                    return (
                        None,
                        Error(
                            description.node,
                            f"Unhandled child of a field with name {field_name} "
                            f"and body: {field_body}"))

            if len(body_blocks) == 0:
                body = ''
            elif len(body_blocks) == 1:
                body = xml.sax.saxutils.escape(body_blocks[0])
            else:
                body = '\n'.join(
                    f'<para>{xml.sax.saxutils.escape(body_block)}</para>'
                    for body_block in body_blocks)

            # endregion

            # region Generate tags in the description

            assert (
                    len(field_name.children) == 1
                    and isinstance(field_name.children[0], docutils.nodes.Text)
            )

            name = field_name.children[0].astext()
            name_parts = name.split()
            if len(name_parts) > 2:
                # TODO: test
                return (
                    None,
                    Error(
                        description.node,
                        f"Expected one or two parts in a field name, "
                        f"but got: {field_name}"))

            if len(name_parts) == 1:
                directive = name_parts[0]
                if directive in ('return', 'returns'):
                    body_indented = textwrap.indent(body, csharp_common.INDENT)
                    blocks.append(Stripped(f'<returns>\n{body_indented}\n</returns>'))
                else:
                    return (
                        None,
                        Error(description.node, f"Unhandled directive: {directive}"))
            elif len(name_parts) == 2:
                directive, directive_arg = name_parts

                if directive == 'param':
                    arg_name = naming.argument_name(directive_arg)

                    if body != "":
                        indented_body = textwrap.indent(body, csharp_common.INDENT)
                        blocks.append(
                            Stripped(
                                f'<param name={xml.sax.saxutils.quoteattr(arg_name)}>\n'
                                f'{indented_body}\n'
                                f'</param>'))
                    else:
                        blocks.append(
                            Stripped(
                                f'<param name={xml.sax.saxutils.quoteattr(arg_name)}>'
                                f'</param>'))
                else:
                    return (
                        None,
                        Error(description.node, f"Unhandled directive: {directive}"))
            else:
                return (
                    None,
                    Error(description.node,
                          f"Expected one or two parts in a field name, "
                          f"but got: {field_name}"))

            # endregion

    # fmt: off
    text = Stripped(
        '\n'.join(
            f'/// {line}'
            for line in '\n'.join(blocks).splitlines()
        ))
    # fmt: on
    return text, None


@require(lambda enum_symbol: not enum_symbol.is_implementation_specific)
def _generate_enum(enum_symbol: intermediate.Enumeration) -> Stripped:
    """Generate the C# code for the enum."""
    writer = io.StringIO()

    if enum_symbol.description is not None:
        comment = _description_comment(enum_symbol.description)
        writer.write(_description_comment(enum_symbol.description))
        writer.write('\n')

    # TODO: continue here
    name = naming.enum_name(enum_symbol.name)
    if len(enum_symbol.literals) == 0:
        writer.write(f"public enum {name}\n{{\n}}")
        return Stripped(writer.getvalue())

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

    return Stripped(writer.getvalue())


@require(lambda enum_symbol: not enum_symbol.is_implementation_specific)
def _generate_interface(
        interface_symbol: intermediate.Interface,
        spec_impls: specific_implementations.SpecificImplementations
) -> Stripped:
    """Generate C# code for the given interface."""
    writer = io.StringIO()

    # TODO: continue here once we figured out the description
    raise NotImplementedError()

    # if interface_symbol.description is not None:
    #     writer.write(_description_comment(interface_symbol.description.strip()))
    #     writer.write("\n")
    #
    # name = naming.interface_name(interface_symbol.name)
    #
    # writer.write(f"public interface {name}\n{{\n")
    #
    # # Code blocks separated by double newlines and indented once
    # codes = []  # type: List[Stripped]
    #
    # # region Getters and setters
    #
    # for prop in interface_symbol.properties:
    #     prop_type = csharp_common.generate_type(prop.type_annotation)
    #     prop_name = naming.property_name(prop.name)
    #
    #     if prop.description is not None:
    #         prop_comment = _description_comment(prop.description.strip())
    #         codes.append(
    #             Stripped(f"{prop_comment}\n{prop_type} {prop_name} {{ get; set; }}"))
    #     else:
    #         codes.append(Code(f"{prop_type} {prop_type} {{ get; set; }}"))
    #
    # for signature in interface_symbol.signatures:
    #     description_blocks = []  # type: List[Rstripped]
    #     if signature.description is not None:
    #         description_blocks.append(
    #             Rstripped(f"<summary>\n{signature.description.strip()}\n</summary>"))
    #
    #     if len(signature.arguments) > 0:
    #         argument_lines = []  # type: List[Rstripped]
    #         for argument in signature.arguments:
    #             # TODO: continue here
    #             raise NotImplementedError()
    #
    #     # fmt: off
    #     returns = (
    #         csharp_common.generate_type(signature.returns)
    #         if signature.returns is not None else "void"
    #     )
    #     # fmt: on
    #
    #     arg_codes = []  # type: List[Stripped]
    #     for arg in signature.arguments:
    #         arg_type = csharp_common.generate_type(arg.type_annotation)
    #         arg_name = naming.argument_name(arg.name)
    #
    #     # TODO: write for methods
    #
    # # endregion
    #
    # # region Methods
    #
    # # endregion
    #
    # for i, code in enumerate(codes):
    #     if i > 0:
    #         writer.write("\n\n")
    #
    #     writer.write(textwrap.indent(code, csharp_common.INDENT))
    # writer.write("\n\n".join(codes))
    # writer.write("\n}}")
    #
    # return Code(writer.getvalue())


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
    # TODO: implement once we figured out the description
    raise NotImplementedError()
    # warning = Stripped(textwrap.dedent("""\
    #     /*
    #      * This code has been automatically generated by aas-core-csharp-codegen.
    #      * Do NOT edit or append.
    #      */"""))
    #
    # blocks = [warning]  # type: List[Rstripped]
    #
    # using_directives = []  # type: List[str]
    # if any(
    #         isinstance(symbol, intermediate.Enumeration)
    #         for symbol in intermediate_symbol_table.symbols
    # ):
    #     using_directives.append(
    #         "using EnumMemberAttribute = "
    #         "System.Runtime.Serialization.EnumMemberAttribute;")
    #
    # if len(using_directives) > 0:
    #     blocks.append(Stripped("\n".join(using_directives)))
    #
    # blocks.append(Stripped(f"namespace {namespace}\n{{"))
    #
    # for intermediate_symbol in intermediate_symbol_table.symbols:
    #     code = None  # type: Optional[Stripped]
    #
    #     if intermediate_symbol.is_implementation_specific:
    #         # TODO: test
    #         code = spec_impls[
    #             specific_implementations.ImplementationKey(
    #                 intermediate_symbol.name)]
    #     else:
    #         if isinstance(intermediate_symbol, intermediate.Enumeration):
    #             # TODO: test
    #             code = _generate_enum(enum_symbol=intermediate_symbol)
    #         elif isinstance(intermediate_symbol, intermediate.Interface):
    #             # TODO: test
    #             code = _generate_interface(
    #                 intermediate_symbol=intermediate_symbol,
    #                 spec_impls=spec_impls)
    #         elif isinstance(intermediate_symbol, intermediate.Class):
    #             # TODO: impl
    #             code = _generate_class(
    #                 intermediate_symbol=intermediate_symbol,
    #                 spec_impls=spec_impls)
    #         else:
    #             assert_never(intermediate_symbol)
    #
    #     assert code is not None
    #     blocks.append(Rstripped(textwrap.indent(code, '    ')))
    #
    # blocks.append(Rstripped(f"}}  // namespace {namespace}"))
    #
    # blocks.append(warning)
    #
    # return '\n\n'.join(blocks)

# endregion

# TODO: implement live_test 🠒 use C# compiler to actually create and compile the code!
