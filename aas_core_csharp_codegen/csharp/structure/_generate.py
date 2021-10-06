"""Generate the C# data structures from the intermediate representation."""
import io
import textwrap
import xml.sax.saxutils
from typing import Optional, Dict, List, Tuple, cast, Union, Sequence

import docutils.nodes
import docutils.parsers.rst.roles
import docutils.utils
from icontract import ensure, require

import aas_core_csharp_codegen.csharp.common as csharp_common
import aas_core_csharp_codegen.csharp.naming as csharp_naming
from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen import specific_implementations
from aas_core_csharp_codegen.common import Error, Identifier, assert_never, \
    Stripped, Rstripped
from aas_core_csharp_codegen.specific_implementations import (
    verify as specific_implementations_verify)
from aas_core_csharp_codegen.understand import (
    constructor as understand_constructor
)


# region Checks

def _verify_structure_name_collisions(
        symbol_table: intermediate.SymbolTable
) -> List[Error]:
    """Verify that the C# names of the structures do not collide."""
    observed_structure_names = {}  # type: Dict[Identifier, intermediate.Symbol]

    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        name = None  # type: Optional[Identifier]

        if isinstance(symbol, intermediate.Class):
            name = csharp_naming.class_name(symbol.name)
        elif isinstance(symbol, intermediate.Enumeration):
            name = csharp_naming.enum_name(symbol.name)
        elif isinstance(symbol, intermediate.Interface):
            name = csharp_naming.interface_name(symbol.name)
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

    for symbol in symbol_table.symbols:
        collision_error = _verify_intra_structure_collisions(intermediate_symbol=symbol)

        if collision_error is not None:
            errors.append(collision_error)

    return errors


def _verify_intra_structure_collisions(
        intermediate_symbol: intermediate.Symbol
) -> Optional[Error]:
    """Verify that no member names collide in the C# structure of the given symbol."""
    errors = []  # type: List[Error]

    if isinstance(intermediate_symbol, intermediate.Interface):
        observed_member_names = {}  # type: Dict[Identifier, str]

        for prop in intermediate_symbol.properties:
            prop_name = csharp_naming.property_name(prop.name)
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

        for signature in intermediate_symbol.signatures:
            method_name = csharp_naming.method_name(signature.name)

            if method_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        signature.parsed.node,
                        f"C# method {method_name!r} corresponding "
                        f"to the meta-model method {signature.name!r} collides with "
                        f"the {observed_member_names[method_name]}"
                    ))
            else:
                observed_member_names[method_name] = (
                    f"C# method {method_name!r} corresponding to "
                    f"the meta-model method {signature.name!r}")

    elif isinstance(intermediate_symbol, intermediate.Class):
        observed_member_names = {}  # type: Dict[Identifier, str]

        for prop in intermediate_symbol.properties:
            prop_name = csharp_naming.property_name(prop.name)
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

        methods_or_signatures = [
        ]  # type: Sequence[Union[intermediate.Method, intermediate.Signature]]

        if isinstance(intermediate_symbol, intermediate.Class):
            methods_or_signatures = intermediate_symbol.methods
        elif isinstance(intermediate_symbol, intermediate.Interface):
            methods_or_signatures = intermediate_symbol.signatures
        else:
            assert_never(intermediate_symbol)

        for signature in methods_or_signatures:
            method_name = csharp_naming.method_name(signature.name)

            if method_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        signature.parsed.node,
                        f"C# method {method_name!r} corresponding "
                        f"to the meta-model method {signature.name!r} collides with "
                        f"the {observed_member_names[method_name]}"
                    ))
            else:
                observed_member_names[method_name] = (
                    f"C# method {method_name!r} corresponding to "
                    f"the meta-model method {signature.name!r}")

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
            cls, symbol_table: intermediate.SymbolTable
    ) -> 'VerifiedIntermediateSymbolTable':
        raise AssertionError("Only for type annotation")


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def verify(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[VerifiedIntermediateSymbolTable], Optional[List[Error]]]:
    """Verify that C# code can be generated from the ``symbol_table``."""
    errors = []  # type: List[Error]

    structure_name_collisions = _verify_structure_name_collisions(
        symbol_table=symbol_table)

    errors.extend(structure_name_collisions)

    for symbol in symbol_table.symbols:
        error = _verify_intra_structure_collisions(intermediate_symbol=symbol)
        if error is not None:
            errors.append(error)

    errors.extend(
        specific_implementations_verify.that_available_for_all_symbols(
            symbol_table=symbol_table,
            spec_impls=spec_impls))

    if len(errors) > 0:
        return None, errors

    return cast(VerifiedIntermediateSymbolTable, symbol_table), None


# endregion

# region Generation

def _render_description_element(
        element: docutils.nodes.Element
) -> Tuple[Optional[str], Optional[str]]:
    """
    Render the element of a description as documentation XML.

    :param element: to be rendered
    :return: the generated code, or error if the paragraph could not be translated
    """
    if isinstance(element, docutils.nodes.Text):
        return xml.sax.saxutils.escape(element.astext()), None

    elif isinstance(element, intermediate.SymbolReferenceInDoc):
        name = None  # type: Optional[str]
        if isinstance(element.symbol, intermediate.Enumeration):
            name = csharp_naming.enum_name(element.symbol.name)
        elif isinstance(element.symbol, intermediate.Interface):
            name = csharp_naming.interface_name(element.symbol.name)
        elif isinstance(element.symbol, intermediate.Class):
            name = csharp_naming.class_name(element.symbol.name)
        else:
            assert_never(element.symbol)

        assert name is not None
        return f'<see cref={xml.sax.saxutils.quoteattr(name)} />', None
    elif isinstance(element, intermediate.PropertyReferenceInDoc):
        prop_name = csharp_naming.property_name(Identifier(element.property_name))
        return f'<see cref={xml.sax.saxutils.quoteattr(prop_name)} />', None

    elif isinstance(element, docutils.nodes.literal):
        return f'<c>{xml.sax.saxutils.escape(element.astext())}</c>', None

    elif isinstance(element, docutils.nodes.paragraph):
        parts = []  # type: List[str]
        for child in element.children:
            text, error = _render_description_element(child)
            if error is not None:
                return None, error

            parts.append(text)

        return ''.join(parts), None

    elif isinstance(element, docutils.nodes.emphasis):
        parts = []  # type: List[str]
        for child in element.children:
            text, error = _render_description_element(child)
            if error is not None:
                return None, error

            parts.append(text)

        return '<em>{}</em>'.format(''.join(parts)), None

    elif isinstance(element, docutils.nodes.list_item):
        parts = []  # type: List[str]
        for child in element.children:
            text, error = _render_description_element(child)
            if error is not None:
                return None, error

            parts.append(text)

        return '<li>{}</li>'.format(''.join(parts)), None

    elif isinstance(element, docutils.nodes.bullet_list):
        parts = ['<ul>\n']
        for child in element.children:
            text, error = _render_description_element(child)
            if error is not None:
                return None, error

            parts.append(f'{text}\n')
        parts.append('</ul>')

        return ''.join(parts), None

    else:
        return None, (
            f"Handling of the element of a description with type {type(element)} "
            f"has not been implemented: {element}"
        )


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _description_comment(
        description: intermediate.Description
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate a documentation comment based on the docstring."""
    if len(description.document.children) == 0:
        return Stripped(""), None

    summary = None  # type: Optional[docutils.nodes.paragraph]
    remarks = None  # type: Optional[List[docutils.nodes.paragraph]]
    # noinspection PyUnusedLocal
    tail = []  # type: List[docutils.nodes.General]

    # Try to match the summary and the remarks
    if (
            len(description.document.children) >= 2
            and isinstance(description.document.children[0], docutils.nodes.paragraph)
            and isinstance(description.document.children[1],
                           (docutils.nodes.paragraph, docutils.nodes.bullet_list))
    ):
        summary = description.document.children[0]

        remarks = [description.document.children[1]]
        last_remark_index = 1
        for child in description.document.children[2:]:
            if isinstance(
                    child, (docutils.nodes.paragraph, docutils.nodes.bullet_list)):
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

    # NOTE (2021-09-16, mristin):
    # We restrict ourselves here quite a lot. This function will need to evolve as
    # we add a larger variety of docstrings to the meta-model.
    #
    # For example, we need to translate ``:paramref:``'s to ``<paramref ...>`` in C#.
    # Additionally, we need to change the name of the argument accordingly (snake_case
    # to camelCase).

    # Blocks to be joined by a new-line
    blocks = []  # type: List[Stripped]

    if summary:
        summary_text, error = _render_description_element(element=summary)
        if error:
            return None, Error(description.node, error)

        blocks.append(
            Stripped(
                f'<summary>\n'
                f'{summary_text}\n'
                f'</summary>'))

    if remarks:
        remark_blocks = []  # type: List[str]
        for remark in remarks:
            remark_text, error = _render_description_element(element=remark)
            if error:
                return None, Error(description.node, error)

            remark_blocks.append(remark_text)

        assert len(remark_blocks) >= 1, \
            f"Expected at least one remark block since ``remarks`` defined: {remarks}"

        if len(remark_blocks) == 1:
            blocks.append(
                Stripped(
                    f'<remarks>\n'
                    f'{remark_blocks[0]}\n'
                    f'</remarks>'))
        else:
            remarks_paras = '\n'.join(
                f'<para>{remark_block}</para>'
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

            body_blocks = []  # type: List[str]
            for body_child in field_body.children:
                body_block, error = _render_description_element(body_child)
                if error:
                    return None, Error(description.node, error)

                body_blocks.append(body_block)

            if len(body_blocks) == 0:
                body = ''
            elif len(body_blocks) == 1:
                body = body_blocks[0]
            else:
                body = '\n'.join(
                    f'<para>{body_block}</para>'
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
                    arg_name = csharp_naming.argument_name(directive_arg)

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


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_enum(
        symbol: intermediate.Enumeration
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the C# code for the enum."""
    writer = io.StringIO()

    if symbol.description is not None:
        comment, error = _description_comment(symbol.description)
        if error:
            return None, error

        writer.write(comment)
        writer.write('\n')

    name = csharp_naming.enum_name(symbol.name)
    if len(symbol.literals) == 0:
        writer.write(f"public enum {name}\n{{\n}}")
        return Stripped(writer.getvalue()), None

    writer.write(f"public enum {name}\n{{\n")
    for i, literal in enumerate(symbol.literals):
        if i > 0:
            writer.write(",\n\n")

        if literal.description:
            literal_comment, error = _description_comment(literal.description)
            if error:
                return None, error

            writer.write(textwrap.indent(literal_comment, csharp_common.INDENT))
            writer.write('\n')

        writer.write(
            textwrap.indent(
                f'[EnumMember(Value = {csharp_common.string_literal(literal.value)})]\n'
                f'{csharp_naming.enum_literal_name(literal.name)}',
                csharp_common.INDENT))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_interface(
        symbol: intermediate.Interface
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate C# code for the given interface."""
    writer = io.StringIO()

    if symbol.description is not None:
        comment, error = _description_comment(symbol.description)
        if error:
            return None, error

        writer.write(comment)
        writer.write("\n")

    name = csharp_naming.interface_name(symbol.name)

    inheritances = list(symbol.inheritances) + [Identifier('Entity')]

    assert len(inheritances) > 0
    if len(inheritances) == 1:
        inheritance = csharp_naming.interface_name(inheritances[0])
        writer.write(f"public interface {name} : {inheritance}\n{{\n")
    else:
        writer.write(f"public interface {name} :\n")
        for i, inheritance in enumerate(
                map(csharp_naming.interface_name, inheritances)):
            if i > 0:
                writer.write(",\n")

            writer.write(textwrap.indent(inheritance, csharp_common.INDENT2))

        writer.write("\n{\n")

    # Code blocks separated by double newlines and indented once
    codes = []  # type: List[Stripped]

    # region Getters and setters

    for prop in symbol.properties:
        prop_type = csharp_common.generate_type(prop.type_annotation)
        prop_name = csharp_naming.property_name(prop.name)

        if prop.description is not None:
            prop_comment, error = _description_comment(prop.description)
            if error:
                return None, error

            codes.append(
                Stripped(f"{prop_comment}\n{prop_type} {prop_name} {{ get; set; }}"))
        else:
            codes.append(Stripped(f"{prop_type} {{ get; set; }}"))

    # endregion

    # region Methods

    for signature in symbol.signatures:
        signature_blocks = []  # type: List[Stripped]

        if signature.description is not None:
            signature_comment, error = _description_comment(signature.description)
            if error:
                return None, error

            signature_blocks.append(signature_comment)

        # fmt: off
        returns = (
            csharp_common.generate_type(signature.returns)
            if signature.returns is not None else "void"
        )
        # fmt: on

        arg_codes = []  # type: List[Stripped]
        for arg in signature.arguments:
            if arg.name == "self":
                continue

            arg_type = csharp_common.generate_type(arg.type_annotation)
            arg_name = csharp_naming.argument_name(arg.name)
            arg_codes.append(Stripped(f'{arg_type} {arg_name}'))

        signature_name = csharp_naming.method_name(signature.name)
        if len(arg_codes) > 2:
            arg_block = ",\n".join(arg_codes)
            arg_block_indented = textwrap.indent(arg_block, csharp_common.INDENT)
            signature_blocks.append(
                Stripped(f"{returns} {signature_name}(\n{arg_block_indented});"))
        elif len(arg_codes) == 1:
            signature_blocks.append(
                Stripped(f"{returns} {signature_name}({arg_codes[0]});"))
        else:
            assert len(arg_codes) == 0
            signature_blocks.append(Stripped(f"{returns} {signature_name}();"))

        codes.append(Stripped("\n".join(signature_blocks)))

    # endregion

    for i, code in enumerate(codes):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(code, csharp_common.INDENT))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _descendable(type_annotation: intermediate.TypeAnnotation) -> bool:
    """Check if the ``type_annotation`` describes an entity or subscribes an entity. """
    if isinstance(type_annotation, intermediate.BuiltinAtomicTypeAnnotation):
        return False
    elif isinstance(type_annotation, intermediate.OurAtomicTypeAnnotation):
        return True
    elif isinstance(type_annotation, intermediate.SelfTypeAnnotation):
        raise AssertionError("Unexpected self type annotation at this layer")
    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        return _descendable(type_annotation=type_annotation.items)
    elif isinstance(type_annotation, intermediate.SequenceTypeAnnotation):
        return _descendable(type_annotation=type_annotation.items)
    elif isinstance(type_annotation, intermediate.SetTypeAnnotation):
        return _descendable(type_annotation=type_annotation.items)
    elif isinstance(type_annotation, intermediate.MappingTypeAnnotation):
        return _descendable(type_annotation=type_annotation.values)
    elif isinstance(type_annotation, intermediate.MutableMappingTypeAnnotation):
        return _descendable(type_annotation=type_annotation.values)
    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        return _descendable(type_annotation=type_annotation.value)
    else:
        assert_never(type_annotation)


def _generate_descend_body(
        symbol: intermediate.Class,
        recurse: bool
)-> Stripped:
    """
    Generate the body of the ``Descend`` and ``DescendOnce`` methods.

    With this function, we can unroll the recursion as a simple optimization
    in the recursive case.
    """
    blocks = []  # type: List[Stripped]

    for prop in symbol.properties:
        type_anno = prop.type_annotation

        if not _descendable(type_annotation=type_anno):
            continue

        prop_name = csharp_naming.property_name(prop.name)

        # Unroll
        stmts = []  # type: List[str]
        item_id = -1  # -1 means we are at the level of the property variable

        @require(lambda an_item_id: an_item_id >= -1)
        def item_var(an_item_id: int) -> Identifier:
            """Generate the item variable used in the loops."""
            if an_item_id == -1:
                return prop_name
            elif an_item_id == 0:
                return Identifier("anItem")
            elif an_item_id == 1:
                return Identifier("anotherItem")
            else:
                return Identifier("yet" + "Yet" * (an_item_id - 2) + "Item")

        while True:
            old_type_anno = type_anno

            if isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
                raise AssertionError(
                    f"Unexpected BuiltinAtomicTypeAnnotation "
                    f"given the descendable property {prop.name!r} of class "
                    f"{symbol.name}")

            elif isinstance(type_anno, intermediate.OurAtomicTypeAnnotation):
                yield_var = item_var(item_id)

                if not recurse:
                    stmts.append(f'yield return {yield_var};')
                else:
                    if _descendable(prop.type_annotation):
                        recurse_var = item_var(item_id + 1)
                        stmts.append(textwrap.dedent(f'''\
                            yield return {yield_var};

                            // Recurse
                            foreach (var {recurse_var} in {yield_var}.Descend())
                            {{
                                yield return {recurse_var};
                            }}'''))
                    else:
                        stmts.append(textwrap.dedent(f'''\
                            yield return {yield_var};
                            
                            // Recursive descent ends here.
                            '''))
                break

            elif isinstance(type_anno, intermediate.SelfTypeAnnotation):
                raise AssertionError("Unexpected self type annotation at this layer")

            elif isinstance(
                    type_anno,
                    (intermediate.ListTypeAnnotation,
                     intermediate.SequenceTypeAnnotation,
                     intermediate.SetTypeAnnotation)):
                item_id += 1
                stmts.append(
                    f"foreach (var {item_var(item_id)} in {item_var(item_id - 1)})")

                # noinspection PyUnresolvedReferences
                type_anno = type_anno.items

            elif isinstance(
                    type_anno,
                    (intermediate.MappingTypeAnnotation,
                     intermediate.MutableMappingTypeAnnotation)):
                item_id += 1

                stmts.append(
                    f"foreach (var {item_var(item_id)} in "
                    f"{item_var(item_id - 1)}.Values)")

                # noinspection PyUnresolvedReferences
                type_anno = type_anno.values

            elif isinstance(type_anno, intermediate.OptionalTypeAnnotation):
                stmts.append(f"if ({item_var(item_id)} != null)")

                type_anno = type_anno.value
            else:
                assert_never(type_anno)

            assert type_anno != old_type_anno, "Loop invariant"

        prefix = []  # type: List[str]
        suffix = []  # type: List[str]

        indent = ''
        for i, stmt in enumerate(stmts):
            if i != len(stmts) - 1:
                prefix.append(f'{indent}{stmt}')
                prefix.append(f'{indent}{{')

                suffix.append(f'{indent}}}')
            else:
                prefix.append(textwrap.indent(stmt, indent))

            indent += csharp_common.INDENT

        blocks.append(Stripped('\n'.join(prefix + suffix)))

    if len(blocks) == 0:
        blocks.append(Stripped('// No descendable properties\nyield return break;'))

    return Stripped('\n\n'.join(blocks))


def _generate_descend_once_method(
        symbol: intermediate.Class
) -> Stripped:
    """Generate the ``DescendOnce`` method for the class of the ``symbol``."""

    body = _generate_descend_body(symbol=symbol, recurse=False)

    indented_body = textwrap.indent(body, csharp_common.INDENT)

    return Stripped(f'''\
/// <summary>
/// Iterate over all the entity instances referenced from this instance 
/// without further recursion.
/// </summary>
public IEnumerable<IEntity> DescendOnce()
{{
{indented_body}
}}''')


def _generate_descend_method(
        symbol: intermediate.Class
) -> Stripped:
    """Generate the recursive ``Descend`` method for the class of the ``symbol``."""

    body = _generate_descend_body(symbol=symbol, recurse=True)

    indented_body = textwrap.indent(body, csharp_common.INDENT)

    return Stripped(f'''\
/// <summary>
/// Iterate recursively over all the entity instances referenced from this instance.
/// </summary>
public IEnumerable<IEntity> Descend()
{{
{indented_body}
}}''')


@require(lambda symbol: symbol.implementation_key is None)
@require(lambda symbol: symbol.constructor.implementation_key is None)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_constructor(
        symbol: intermediate.Class
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the constructor function for the given symbol."""
    cls_name = csharp_naming.class_name(symbol.name)

    blocks = []  # type: List[str]

    # TODO: handle default values
    arg_codes = []  # type: List[str]
    for arg in symbol.constructor.arguments:
        if arg.name == "self":
            continue

        arg_type = csharp_common.generate_type(arg.type_annotation)
        arg_name = csharp_naming.argument_name(arg.name)
        arg_codes.append(Stripped(f'{arg_type} {arg_name}'))

    if len(arg_codes) == 0:
        return (None, Error(
            symbol.parsed.node,
            "An empty constructor is automatically generated, "
            "which conflicts with the empty constructor "
            "specified in the meta-model"))

    elif len(arg_codes) == 1:
        blocks.append(f"{cls_name}({arg_codes[0]})\n{{")
    else:
        arg_block = ",\n".join(arg_codes)
        arg_block_indented = textwrap.indent(arg_block, csharp_common.INDENT)
        blocks.append(
            Stripped(f"{cls_name}(\n{arg_block_indented})\n{{"))

    body = []  # type: List[str]
    for stmt in symbol.constructor.statements:
        if isinstance(stmt, understand_constructor.AssignArgument):
            if stmt.default is None:
                body.append(
                    f'{csharp_naming.property_name(stmt.name)} = '
                    f'{csharp_naming.argument_name(stmt.argument)};')
            else:
                if isinstance(stmt.default, understand_constructor.EmptyList):
                    prop = symbol.property_map[stmt.name]
                    prop_type = csharp_common.generate_type(prop.type_annotation)

                    arg_name = csharp_naming.argument_name(stmt.argument)

                    # Write the assignment as a ternary operator
                    writer = io.StringIO()
                    writer.write(f'{csharp_naming.property_name(stmt.name)} = ')
                    writer.write(
                        f'({arg_name} != null)\n')
                    writer.write(
                        textwrap.indent(f'? {arg_name}\n', csharp_common.INDENT))
                    writer.write(
                        textwrap.indent(
                            f': new {prop_type}();', csharp_common.INDENT))

                    body.append(writer.getvalue())
                elif isinstance(
                        stmt.default, understand_constructor.DefaultEnumLiteral):
                    literal_code = ".".join([
                        csharp_naming.enum_name(stmt.default.enum.name),
                        csharp_naming.enum_literal_name(stmt.default.literal.name)
                    ])

                    body.append(
                        f'{csharp_naming.property_name(stmt.name)} = '
                        f'{literal_code};')
                else:
                    assert_never(stmt.default)

        else:
            assert_never(stmt)

    blocks.append(
        '\n'.join(
            textwrap.indent(stmt_code, csharp_common.INDENT)
            for stmt_code in body))

    blocks.append("}")

    return Stripped("\n".join(blocks)), None


@require(lambda symbol: symbol.implementation_key is None)
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_class(
        symbol: intermediate.Class,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate C# code for the given class."""
    writer = io.StringIO()

    if symbol.description is not None:
        comment, error = _description_comment(symbol.description)
        if error:
            return None, error

        writer.write(comment)
        writer.write("\n")

    name = csharp_naming.class_name(symbol.name)

    interfaces = list(symbol.interfaces) + [Identifier('Entity')]

    assert len(interfaces) > 0
    if len(interfaces) == 1:
        interface_name = csharp_naming.interface_name(interfaces[0])
        writer.write(f"public class {name} : {interface_name}\n{{\n")
    else:
        writer.write(f"public class {name} :\n")
        for i, interface_name in enumerate(
                map(csharp_naming.interface_name, interfaces)):
            if i > 0:
                writer.write(",\n")

            writer.write(textwrap.indent(interface_name, csharp_common.INDENT2))

        writer.write("\n{\n")

    # Code blocks separated by double newlines and indented once
    blocks = []  # type: List[Stripped]

    # region Getters and setters

    for prop in symbol.properties:
        prop_type = csharp_common.generate_type(prop.type_annotation)
        prop_name = csharp_naming.property_name(prop.name)

        prop_blocks = []  # type: List[Stripped]

        if prop.description is not None:
            prop_comment, error = _description_comment(prop.description)
            if error:
                return None, error

            prop_blocks.append(prop_comment)

        prop_blocks.append(Stripped(f"{prop_type} {prop_name} {{ get; set; }}"))

        blocks.append(Stripped('\n'.join(prop_blocks)))

    # endregion

    # region Methods

    for method in symbol.methods:
        if method.implementation_key is not None:
            blocks.append(spec_impls[method.implementation_key])
        else:
            # NOTE (mristin, 2021-09-16):
            # At the moment, we do not transpile the method body and its contracts.
            # We want to finish the meta-model for the V3 and fix de/serialization
            # before taking on this rather hard task.

            return (None, Error(
                symbol.parsed.node,
                "At the moment, we do not transpile the method body and "
                "its contracts."))

    blocks.append(_generate_descend_once_method(symbol=symbol))
    blocks.append(_generate_descend_method(symbol=symbol))

    blocks.append(
        Stripped(
            textwrap.dedent(f'''\
                /// <summary>
                /// Accept the visitor to visit this instance for double dispatch.
                /// </summary>
                public Accept<T>(IVisitor<T> visitor)
                {{
                {csharp_common.INDENT}visitor.visit(this);
                }}''')))

    # endregion

    # region Constructor

    if symbol.constructor.implementation_key is not None:
        blocks.append(spec_impls[symbol.constructor.implementation_key])
    else:
        constructor_block, error = _generate_constructor(symbol=symbol)
        if error is not None:
            return None, error

        blocks.append(constructor_block)

    # endregion

    for i, code in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(code, csharp_common.INDENT))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None

# TODO: implement default constructor (setting all props to defaults)


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
        namespace: csharp_common.NamespaceIdentifier,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code of the structures based on the symbol table.

    The ``namespace`` defines the C# namespace.
    """
    blocks = [csharp_common.WARNING]  # type: List[Rstripped]

    using_directives = [
        "using EnumMemberAttribute = System.Runtime.Serialization.EnumMemberAttribute;",
        "using System.Collections.Generic;  // can't alias"
    ]  # type: List[str]

    if len(using_directives) > 0:
        blocks.append(Stripped("\n".join(using_directives)))

    blocks.append(Stripped(f"namespace {namespace}\n{{"))

    blocks.append(Rstripped(
            textwrap.indent(
                textwrap.dedent('''\
                    /// <summary>
                    /// Represent a general entity of an AAS model.
                    /// </summary>
                    public interface IEntity
                    {
                        /// <summary>
                        /// Iterate over all the entity instances referenced from this instance 
                        /// without further recursion.
                        /// </summary>
                        public IEnumerable<IEntity> DescendOnce();
                        
                        /// <summary>
                        /// Iterate recursively over all the entity instances referenced from this instance.
                        /// </summary>
                        public IEnumerable<IEntity> Descend();

                        
                        /// <summary>
                        /// Accept the visitor to visit this instance for double dispatch.
                        /// </summary>
                        public Accept<T>(IVisitor<T> visitor);
                    }'''),
                csharp_common.INDENT)))

    errors = []  # type: List[Error]

    for intermediate_symbol in symbol_table.symbols:
        code = None  # type: Optional[Stripped]
        error = None  # type: Optional[Error]

        if (
                isinstance(intermediate_symbol, intermediate.Class)
                and intermediate_symbol.implementation_key is not None
        ):
            code = spec_impls[intermediate_symbol.implementation_key]
        else:
            if isinstance(intermediate_symbol, intermediate.Enumeration):
                # TODO: test
                code, error = _generate_enum(symbol=intermediate_symbol)
            elif isinstance(intermediate_symbol, intermediate.Interface):
                # TODO: test
                code, error = _generate_interface(
                    symbol=intermediate_symbol)

            elif isinstance(intermediate_symbol, intermediate.Class):
                code, error = _generate_class(
                    symbol=intermediate_symbol,
                    spec_impls=spec_impls)
            else:
                assert_never(intermediate_symbol)

        assert (code is None) ^ (error is None)
        if error is not None:
            errors.append(error)
        else:
            assert code is not None
            blocks.append(Rstripped(textwrap.indent(code, '    ')))

    if len(errors) > 0:
        return None, errors

    blocks.append(Rstripped(f"}}  // namespace {namespace}"))

    blocks.append(csharp_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write('\n\n')

        out.write(block)

    out.write('\n')

    return out.getvalue(), None

# endregion

# TODO: implement live_test 🠒 use C# compiler to actually create and compile the code!
