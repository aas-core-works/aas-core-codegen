"""Render descriptions to C# documentation comments."""
import textwrap
from typing import Tuple, Optional, List
import xml.sax.saxutils

from icontract import ensure
import docutils.nodes
import docutils.parsers.rst.roles
import docutils.utils

from aas_core_codegen.common import Stripped, Error, assert_never, Identifier
from aas_core_codegen import intermediate
from aas_core_codegen.intermediate import (
    rendering as intermediate_rendering
)
from aas_core_codegen.csharp import (
    naming as csharp_naming,
)
from aas_core_codegen.csharp.common import INDENT as I


class _ElementRenderer(
    intermediate_rendering.DocutilsElementTransformer[str]
):
    """Render descriptions as C# docstring XML."""

    def transform_text(
            self, element: docutils.nodes.Text
    ) -> Tuple[Optional[str], Optional[str]]:
        return xml.sax.saxutils.escape(element.astext()), None

    def transform_symbol_reference_in_doc(
            self, element: intermediate.SymbolReferenceInDoc
    ) -> Tuple[Optional[str], Optional[str]]:
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
        return f"<see cref={xml.sax.saxutils.quoteattr(name)} />", None

    def transform_attribute_reference_in_doc(
            self, element: intermediate.AttributeReferenceInDoc
    ) -> Tuple[Optional[str], Optional[str]]:
        cref = None  # type: Optional[str]

        if isinstance(element.reference, intermediate.PropertyReferenceInDoc):
            symbol_name = None  # type: Optional[str]

            if isinstance(element.reference.symbol, intermediate.Class):
                symbol_name = csharp_naming.class_name(element.reference.symbol.name)
            elif isinstance(element.reference.symbol, intermediate.Interface):
                symbol_name = csharp_naming.class_name(element.reference.symbol.name)
            else:
                assert_never(element.reference.symbol)

            prop_name = csharp_naming.property_name(element.reference.prop.name)

            assert symbol_name is not None
            cref = f"{symbol_name}.{prop_name}"
        elif isinstance(
                element.reference, intermediate.EnumerationLiteralReferenceInDoc):
            symbol_name = csharp_naming.enum_name(element.reference.symbol.name)
            literal_name = csharp_naming.enum_literal_name(
                element.reference.literal.name)

            cref = f"{symbol_name}.{literal_name}"
        else:
            assert_never(element.reference)

        assert cref is not None
        return f"<see cref={xml.sax.saxutils.quoteattr(cref)} />", None

    def transform_argument_reference_in_doc(
            self, element: intermediate.ArgumentReferenceInDoc
    ) -> Tuple[Optional[str], Optional[str]]:
        arg_name = csharp_naming.argument_name(Identifier(element.reference))
        return f"<paramref name={xml.sax.saxutils.quoteattr(arg_name)} />", None

    def transform_literal(
            self, element: docutils.nodes.literal
    ) -> Tuple[Optional[str], Optional[str]]:
        return f"<c>{xml.sax.saxutils.escape(element.astext())}</c>", None

    def transform_paragraph(
            self, element: docutils.nodes.paragraph
    ) -> Tuple[Optional[str], Optional[str]]:
        parts = []  # type: List[str]
        for child in element.children:
            text, error = self.transform(child)
            if error is not None:
                return None, error

            assert text is not None
            parts.append(text)

        return "".join(parts), None

    def transform_emphasis(
            self, element: docutils.nodes.emphasis
    ) -> Tuple[Optional[str], Optional[str]]:
        parts = []  # type: List[str]
        for child in element.children:
            text, error = self.transform(child)
            if error is not None:
                return None, error

            assert text is not None
            parts.append(text)

        return "<em>{}</em>".format("".join(parts)), None

    def transform_list_item(
            self, element: docutils.nodes.list_item
    ) -> Tuple[Optional[str], Optional[str]]:
        parts = []  # type: List[str]
        for child in element.children:
            text, error = self.transform(child)
            if error is not None:
                return None, error

            assert text is not None
            parts.append(text)

        return "<li>{}</li>".format("".join(parts)), None

    def transform_bullet_list(
            self, element: docutils.nodes.bullet_list
    ) -> Tuple[Optional[str], Optional[str]]:
        parts = ["<ul>\n"]
        for child in element.children:
            text, error = self.transform(child)
            if error is not None:
                return None, error

            assert text is not None
            parts.append(f"{text}\n")
        parts.append("</ul>")

        return "".join(parts), None

    def transform_note(
            self, element: docutils.nodes.note
    ) -> Tuple[Optional[str], Optional[str]]:
        parts = []  # type: List[str]
        for child in element.children:
            text, error = self.transform(child)
            if error is not None:
                return None, error

            assert text is not None
            parts.append(text)

        return "".join(parts), None

    def transform_reference(
            self, element: docutils.nodes.reference
    ) -> Tuple[Optional[str], Optional[str]]:
        parts = []  # type: List[str]
        for child in element.children:
            text, error = self.transform(child)
            if error is not None:
                return None, error

            assert text is not None
            parts.append(text)

        return "".join(parts), None

    def transform_document(
            self, element: docutils.nodes.document
    ) -> Tuple[Optional[str], Optional[str]]:
        if len(element.children) == 0:
            return "", None

        summary = None  # type: Optional[docutils.nodes.paragraph]
        remarks = []  # type: Optional[List[docutils.nodes.Element]]
        tail = []  # type: List[docutils.nodes.Element]

        # Try to match the summary and the remarks
        if len(element.children) >= 1:
            if not isinstance(element.children[0], docutils.nodes.paragraph):
                return None, (
                    f"Expected the first document element to be a summary and "
                    f"thus a paragraph, but got: {element.children[0]}"
                )

            summary = element.children[0]

        remainder = element.children[1:]
        for i, child in enumerate(remainder):
            if isinstance(
                    child,
                    (docutils.nodes.paragraph,
                     docutils.nodes.bullet_list,
                     docutils.nodes.note)):
                remarks.append(child)
            else:
                tail = remainder[i:]
                break

        # NOTE (2021-09-16, mristin):
        # We restrict ourselves here quite a lot. This function will need to evolve as
        # we add a larger variety of docstrings to the meta-model.
        #
        # For example, we need to translate ``:paramref:``'s to ``<paramref ...>`` in
        # C#. Additionally, we need to change the name of the argument accordingly
        # (``snake_case`` to ``camelCase``).

        # Blocks to be joined by a new-line
        blocks = []  # type: List[Stripped]

        renderer = _ElementRenderer()

        if summary:
            summary_text, error = renderer.transform(element=summary)
            if error:
                return None, error

            assert summary_text is not None
            blocks.append(Stripped(f"<summary>\n" f"{summary_text}\n" f"</summary>"))

        if remarks:
            remark_blocks = []  # type: List[str]
            for remark in remarks:
                remark_text, error = renderer.transform(element=remark)
                if error:
                    return None, error

                assert remark_text is not None
                remark_blocks.append(remark_text)

            assert len(remark_blocks) >= 1, (
                f"Expected at least one remark block "
                f"since ``remarks`` defined: {remarks}"
            )

            if len(remark_blocks) == 1:
                blocks.append(
                    Stripped(f"<remarks>\n" f"{remark_blocks[0]}\n" f"</remarks>")
                )
            else:
                remarks_paras = "\n".join(
                    f"<para>{remark_block}</para>" for remark_block in remark_blocks
                )

                blocks.append(
                    Stripped(f"<remarks>\n" f"{remarks_paras}\n" f"</remarks>")
                )

        for tail_element in tail:
            # TODO-BEFORE-RELEASE (mristin, 2021-12-13): test
            if not isinstance(tail_element, docutils.nodes.field_list):
                return None, (
                    f"Expected only a field list to follow the summary and remarks, "
                    f"but got: {tail_element}"
                )

            for field in tail_element.children:
                assert len(field.children) == 2
                field_name, field_body = field.children
                assert isinstance(field_name, docutils.nodes.field_name)
                assert isinstance(field_body, docutils.nodes.field_body)

                # region Generate field body

                body_blocks = []  # type: List[str]
                for body_child in field_body.children:
                    body_block, error = renderer.transform(body_child)
                    if error:
                        return None, error

                    body_blocks.append(body_block)

                if len(body_blocks) == 0:
                    body = ""
                elif len(body_blocks) == 1:
                    body = body_blocks[0]
                else:
                    body = "\n".join(
                        f"<para>{body_block}</para>" for body_block in body_blocks
                    )

                # endregion

                # region Generate tags in the description

                assert len(field_name.children) == 1 and isinstance(
                    field_name.children[0], docutils.nodes.Text
                )

                name = field_name.children[0].astext()
                name_parts = name.split()
                if len(name_parts) > 2:
                    # TODO-BEFORE-RELEASE (mristin, 2021-12-13): test
                    return (
                        None,
                        f"Expected one or two parts in a field name, "
                        f"but got: {field_name}",
                    )

                if len(name_parts) == 1:
                    directive = name_parts[0]
                    if directive in ("return", "returns"):
                        body_indented = textwrap.indent(body, I)
                        blocks.append(
                            Stripped(f"<returns>\n{body_indented}\n</returns>")
                        )
                    else:
                        return None, f"Unhandled directive: {directive}"

                elif len(name_parts) == 2:
                    directive, directive_arg = name_parts

                    if directive == "param":
                        arg_name = csharp_naming.argument_name(directive_arg)

                        if body != "":
                            indented_body = textwrap.indent(body, I)
                            blocks.append(
                                Stripped(
                                    f"<param name={xml.sax.saxutils.quoteattr(arg_name)}>\n"
                                    f"{indented_body}\n"
                                    f"</param>"
                                )
                            )
                        else:
                            blocks.append(
                                Stripped(
                                    f"<param name={xml.sax.saxutils.quoteattr(arg_name)}>"
                                    f"</param>"
                                )
                            )
                    else:
                        return None, f"Unhandled directive: {directive}"
                else:
                    return (
                        None,
                        f"Expected one or two parts in a field name, "
                        f"but got: {field_name}",
                    )

                # endregion

        # fmt: off
        text = '\n'.join(
            f'/// {line}'
            for line in '\n'.join(blocks).splitlines()
        )
        # fmt: on
        return text, None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def generate_comment(
        description: intermediate.Description,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate a documentation comment based on the docstring."""
    if len(description.document.children) == 0:
        return Stripped(""), None

    renderer = _ElementRenderer()
    text, error = renderer.transform(description.document)
    if error:
        return None, Error(description.node, error)

    assert text is not None
    return Stripped(text), None
