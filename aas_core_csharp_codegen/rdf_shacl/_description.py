"""Render the description of a class or a property as a plain text."""
import xml.sax.saxutils
from typing import Optional, List, Tuple

import docutils.nodes
from icontract import ensure

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Identifier
from aas_core_csharp_codegen.intermediate import (
    rendering as intermediate_rendering
)
from aas_core_csharp_codegen.rdf_shacl import (
    naming as rdf_shacl_naming
)


class Token:
    """Represent a token of a rendered description."""


class TokenText(Token):
    """Represent a text without a break."""

    def __init__(self, content: str) -> None:
        """Initialize with the given values."""
        self.content = content


class TokenParagraphBreak(Token):
    """Represent a paragraph break in a rendered description."""


class TokenLineBreak(Token):
    """Represent a line break in a rendered description."""


class Renderer(
    intermediate_rendering.DocutilsElementTransformer[List[Token]]):
    """Render descriptions as C# docstring XML."""

    def transform_text(
            self, element: docutils.nodes.Text
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        return [TokenText(element.astext())], None

    def transform_symbol_reference_in_doc(
            self, element: intermediate.SymbolReferenceInDoc
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        cls_name = rdf_shacl_naming.class_name(element.symbol.name)
        return [TokenText(f"'{cls_name}'")], None

    def transform_property_reference_in_doc(
            self, element: intermediate.PropertyReferenceInDoc
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        prop_name = rdf_shacl_naming.property_name(Identifier(element.property_name))
        return [TokenText(f"'{prop_name}'")], None

    def transform_literal(
            self, element: docutils.nodes.literal
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        return [TokenText(element.astext())], None

    def transform_paragraph(
            self, element: docutils.nodes.paragraph
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        tokens = []  # type: List[Token]
        for child in element.children:
            child_tokens, error = self.transform(child)
            if error is not None:
                return None, error

            assert child_tokens is not None
            tokens.extend(child_tokens)

        tokens.append(TokenParagraphBreak())

        return tokens, None

    def transform_emphasis(
            self, element: docutils.nodes.emphasis
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        tokens = []  # type: List[Token]
        for child in element.children:
            child_tokens, error = self.transform(child)
            if error is not None:
                return None, error

            assert child_tokens is not None
            tokens.extend(child_tokens)

        return tokens, None

    # fmt: off
    @ensure(
        lambda result:
        not (result[0] is not None)
        or (
            len(result[0]) > 0
            and not isinstance(result[-1], TokenLineBreak)
            and not any(
                isinstance(token, TokenParagraphBreak)
                for token in result[0]
            )
        )
    )
    # fmt: on
    def transform_list_item(
            self, element: docutils.nodes.list_item
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        tokens = []  # type: List[Token]

        if len(element.children) == 0:
            return (
                [TokenText("* (empty)")], None
            )

        for child in element.children:
            child_tokens, error = self.transform(child)
            if error is not None:
                return None, error

            if any(isinstance(token, TokenParagraphBreak) for token in
                   child_tokens):
                return None, f'Unexpected paragraph break in the list item: {element}'

            # Indent the line breaks
            lines = []  # type: List[List[TokenText]]
            line = []  # type: List[TokenText]
            for token in child_tokens:
                if isinstance(token, TokenLineBreak):
                    lines.append(line)
                    line = []
                elif isinstance(token, TokenText):
                    line.append(token)
                else:
                    raise AssertionError(f"Unexpected token: {token}")

            for i, line in enumerate(lines):
                if i == 0:
                    tokens.append(TokenText("* "))
                    tokens.extend(line)
                else:
                    tokens.append(TokenLineBreak())
                    tokens.append(TokenText("  "))
                    tokens.extend(line)

        return tokens, None

    def transform_bullet_list(
            self, element: docutils.nodes.bullet_list
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        tokens = []  # type: List[Token]
        for child in element.children:
            child_tokens, error = self.transform(child)
            if error is not None:
                return None, error

            assert child_tokens is not None
            tokens.extend(child_tokens)
            tokens.append(TokenLineBreak())

        return tokens, None
