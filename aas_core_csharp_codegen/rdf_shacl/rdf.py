"""Generate the RDF ontology based on the meta-model."""
import enum
import io
from typing import Union, Tuple, Optional, List

import docutils
import docutils.nodes
from icontract import ensure

from aas_core_csharp_codegen import intermediate, specific_implementations
from aas_core_csharp_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_csharp_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common
)
from aas_core_csharp_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II
)


class _DescriptionToken:
    """Represent a token of a rendered description."""


class _DescriptionTokenText(_DescriptionToken):
    """Represent a text without a break."""

    def __init__(self, content: str) -> None:
        """Initialize with the given values."""
        self.content = content


class _DescriptionTokenParagraphBreak(_DescriptionToken):
    """Represent a paragraph break in a rendered description."""


class _DescriptionTokenLineBreak(_DescriptionToken):
    """Represent a line break in a rendered description."""


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _render_description_element(
        element: docutils.nodes.Element
) -> Tuple[Optional[List[_DescriptionToken]], Optional[str]]:
    """
    Render the element of a description as plain text.

    :param element: to be rendered
    :return: the generated text, or error if the paragraph could not be translated
    """
    if isinstance(element, docutils.nodes.Text):
        return [_DescriptionTokenText(element.astext())], None

    elif isinstance(element, intermediate.SymbolReferenceInDoc):
        cls_name = rdf_shacl_naming.class_name(element.symbol.name)
        return [_DescriptionTokenText(f"'{cls_name}'")], None

    elif isinstance(element, intermediate.PropertyReferenceInDoc):
        prop_name = rdf_shacl_naming.property_name(Identifier(element.property_name))
        return [_DescriptionTokenText(f"'{prop_name}'")], None

    elif isinstance(element, docutils.nodes.literal):
        return [_DescriptionTokenText(element.astext())], None

    elif isinstance(element, docutils.nodes.paragraph):
        tokens = []  # type: List[_DescriptionToken]
        for child in element.children:
            child_tokens, error = _render_description_element(child)
            if error is not None:
                return None, error

            assert child_tokens is not None
            tokens.extend(child_tokens)

        return tokens, None

    elif isinstance(element, docutils.nodes.emphasis):
        tokens = []  # type: List[_DescriptionToken]
        for child in element.children:
            child_tokens, error = _render_description_element(child)
            if error is not None:
                return None, error

            assert child_tokens is not None
            tokens.extend(child_tokens)

        return tokens, None

    elif isinstance(element, docutils.nodes.list_item):
        tokens = []  # type: List[_DescriptionToken]

        if len(element.children) == 0:
            return (
                [_DescriptionTokenText("* (empty)"), _DescriptionTokenLineBreak], None
            )

        for child in element.children:
            child_tokens, error = _render_description_element(child)
            if error is not None:
                return None, error

            if any(isinstance(token, _DescriptionTokenParagraphBreak) for token in
                   child_tokens):
                return None, f'Unexpected paragraph break in the list item: {element}'

            # Indent the line breaks
            lines = []  # type: List[List[_DescriptionTokenText]]
            line = []  # type: List[_DescriptionTokenText]
            for token in child_tokens:
                if isinstance(token, _DescriptionTokenLineBreak):
                    lines.append(line)
                    line = []
                elif isinstance(token, _DescriptionTokenText):
                    line.append(token)
                else:
                    raise AssertionError(f"Unexpected token: {token}")

            for i, line in enumerate(lines):
                if i == 0:
                    tokens.append(_DescriptionTokenText("* "))
                    tokens.extend(line)
                else:
                    tokens.append(_DescriptionTokenText("  "))
                    tokens.extend(line)

                tokens.append(_DescriptionTokenLineBreak())

        tokens.append(_DescriptionTokenLineBreak())

        return tokens, None

    elif isinstance(element, docutils.nodes.bullet_list):
        tokens = []  # type: List[_DescriptionToken]
        for child in element.children:
            child_tokens, error = _render_description_element(child)
            if error is not None:
                return None, error

            assert child_tokens is not None
            tokens.extend(child_tokens)

        return ''.join(parts), None

    else:
        return None, (
            f"Handling of the element of a description with type {type(element)} "
            f"has not been implemented: {element}"
        )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_comment(
        description: intermediate.Description
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """
    Generate the comment text based on the description.

    The description might come either from an interface or a class, or from
    a property.
    """
    if len(description.document.children) == 0:
        return Stripped(""), None

    # # Blocks to be joined by a new-line
    # blocks = []  # type: List[Stripped]
    #
    # if summary:
    #     summary_text, error = _render_description_element(element=summary)
    #     if error:
    #         return None, Error(description.node, error)
    #
    #     blocks.append(
    #         Stripped(
    #             f'<summary>\n'
    #             f'{summary_text}\n'
    #             f'</summary>'))
    #
    # if remarks:
    #     remark_blocks = []  # type: List[str]
    #     for remark in remarks:
    #         remark_text, error = _render_description_element(element=remark)
    #         if error:
    #             return None, Error(description.node, error)
    #
    #         remark_blocks.append(remark_text)
    #
    #     assert len(remark_blocks) >= 1, \
    #         f"Expected at least one remark block since ``remarks`` defined: {remarks}"
    #
    #     if len(remark_blocks) == 1:
    #         blocks.append(
    #             Stripped(
    #                 f'<remarks>\n'
    #                 f'{remark_blocks[0]}\n'
    #                 f'</remarks>'))
    #     else:
    #         remarks_paras = '\n'.join(
    #             f'<para>{remark_block}</para>'
    #             for remark_block in remark_blocks)
    #
    #         blocks.append(
    #             Stripped(
    #                 f'<remarks>\n'
    #                 f'{remarks_paras}\n'
    #                 f'</remarks>'))
    #
    # for tail_element in tail:
    #     # TODO: test
    #     if not isinstance(tail_element, docutils.nodes.field_list):
    #         return (
    #             None,
    #             Error(
    #                 description.node,
    #                 f"Expected only a field list to follow the summary and remarks, "
    #                 f"but got: {tail_element}"))
    #
    #     for field in tail_element.children:
    #         assert len(field.children) == 2
    #         field_name, field_body = field.children
    #         assert isinstance(field_name, docutils.nodes.field_name)
    #         assert isinstance(field_body, docutils.nodes.field_body)
    #
    #         # region Generate field body
    #
    #         body_blocks = []  # type: List[str]
    #         for body_child in field_body.children:
    #             body_block, error = _render_description_element(body_child)
    #             if error:
    #                 return None, Error(description.node, error)
    #
    #             body_blocks.append(body_block)
    #
    #         if len(body_blocks) == 0:
    #             body = ''
    #         elif len(body_blocks) == 1:
    #             body = body_blocks[0]
    #         else:
    #             body = '\n'.join(
    #                 f'<para>{body_block}</para>'
    #                 for body_block in body_blocks)
    #
    #         # endregion
    #
    #         # region Generate tags in the description
    #
    #         assert (
    #                 len(field_name.children) == 1
    #                 and isinstance(field_name.children[0], docutils.nodes.Text)
    #         )
    #
    #         name = field_name.children[0].astext()
    #         name_parts = name.split()
    #         if len(name_parts) > 2:
    #             # TODO: test
    #             return (
    #                 None,
    #                 Error(
    #                     description.node,
    #                     f"Expected one or two parts in a field name, "
    #                     f"but got: {field_name}"))
    #
    #         if len(name_parts) == 1:
    #             directive = name_parts[0]
    #             if directive in ('return', 'returns'):
    #                 body_indented = textwrap.indent(body, csharp_common.INDENT)
    #                 blocks.append(Stripped(f'<returns>\n{body_indented}\n</returns>'))
    #             else:
    #                 return (
    #                     None,
    #                     Error(description.node, f"Unhandled directive: {directive}"))
    #         elif len(name_parts) == 2:
    #             directive, directive_arg = name_parts
    #
    #             if directive == 'param':
    #                 arg_name = csharp_naming.argument_name(directive_arg)
    #
    #                 if body != "":
    #                     indented_body = textwrap.indent(body, csharp_common.INDENT)
    #                     blocks.append(
    #                         Stripped(
    #                             f'<param name={xml.sax.saxutils.quoteattr(arg_name)}>\n'
    #                             f'{indented_body}\n'
    #                             f'</param>'))
    #                 else:
    #                     blocks.append(
    #                         Stripped(
    #                             f'<param name={xml.sax.saxutils.quoteattr(arg_name)}>'
    #                             f'</param>'))
    #             else:
    #                 return (
    #                     None,
    #                     Error(description.node, f"Unhandled directive: {directive}"))
    #         else:
    #             return (
    #                 None,
    #                 Error(description.node,
    #                       f"Expected one or two parts in a field name, "
    #                       f"but got: {field_name}"))
    #
    #         # endregion
    #
    # # fmt: off
    # text = Stripped(
    #     '\n'.join(
    #         f'/// {line}'
    #         for line in '\n'.join(blocks).splitlines()
    #     ))
    # # fmt: on
    # return text, None


def _define_owl_class(
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped
) -> Stripped:
    """Generate the code to define an OWL class."""
    cls_name = rdf_shacl_naming.class_name(symbol.name)

    writer = io.StringIO()
    writer.write(f'### {url_prefix}/{cls_name}\n')
    writer.write(f'aas:{cls_name} rdf:type owl:Class ;\n')

    if symbol.description is not None:
        comment = _generate_comment(symbol.description)

        writer.write(
            f'{I}rdfs:comment {rdf_shacl_common.string_literal(comment)}@en ;\n')

    cls_label = rdf_shacl_naming.class_label(symbol.name)
    writer.write(
        f'{I}rdfs:label {rdf_shacl_common.string_literal(cls_label)}^^xsd:string ;\n')

    writer.write('.')
    return Stripped(writer.getvalue())


def _define_for_class_or_interface(
        symbol: Union[intermediate.Interface, intermediate.Class],
        url_prefix: Stripped
) -> Stripped:
    """Generate the definition for the intermediate ``symbol``."""
    blocks = [
        _define_owl_class(symbol=symbol, url_prefix=url_prefix)
    ]  # type: List[Stripped]

    return Stripped('\n\n'.join(blocks))


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the JSON schema based on the ``symbol_table."""
    errors = []  # type: List[Error]

    preamble_key = specific_implementations.ImplementationKey(
        "rdf/preamble.ttl"
    )
    preamble = spec_impls.get(preamble_key, None)
    if preamble is None:
        errors.append(Error(
            None,
            f"The implementation snippet for the RDF preamble "
            f"is missing: {preamble_key}"))

    url_prefix_key = specific_implementations.ImplementationKey(
        "rdf/url_prefix.txt"
    )
    url_prefix = spec_impls.get(url_prefix_key, None)
    if url_prefix is None:
        errors.append(Error(
            None,
            f"The implementation snippet for the URL prefix of the ontology "
            f"is missing: {url_prefix_key}"))

    if len(errors) > 0:
        return None, errors

    blocks = [
        preamble
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        block = None  # type: Optional[Stripped]

        if isinstance(symbol, intermediate.Enumeration):
            block = _define_for_enumeration(enumeration=symbol)
        elif isinstance(symbol, (intermediate.Interface, intermediate.Class)):
            block = _define_for_class_or_interface(symbol=symbol)
        else:
            assert_never(symbol)

        assert block is not None
        blocks.append(block)

    return Stripped('\n\n'.join(blocks)), None
