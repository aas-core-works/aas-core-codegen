"""Render the description of a class or a property as a plain text."""
import xml.sax.saxutils
from typing import Optional, List, Tuple, Sequence

import docutils.nodes
from icontract import ensure

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Identifier
from aas_core_csharp_codegen.intermediate import (
    rendering as intermediate_rendering
)
from aas_core_csharp_codegen.intermediate.rendering import T
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

    def __repr__(self) -> str:
        return f"{TokenText.__name__}({self.content!r})"


class TokenParagraphBreak(Token):
    """Represent a paragraph break in a rendered description."""

    def __repr__(self) -> str:
        return f"{TokenParagraphBreak.__name__}()"


class TokenLineBreak(Token):
    """Represent a line break in a rendered description."""

    def __repr__(self) -> str:
        return f"{TokenLineBreak.__name__}()"


def without_redundant_breaks(tokens: Sequence[Token]) -> List[Token]:
    """Remove the redundant breaks from ``tokens`` and return a cleaned-up list."""
    if len(tokens) == 0:
        return []

    last_token = None  # type: Optional[Token]
    result = []  # type: List[Token]

    # region Remove multiple consecutive paragraph breaks and line breaks

    for token in tokens:
        if last_token is None:
            result.append(token)
        elif (
                isinstance(last_token, TokenLineBreak)
                and isinstance(token, TokenLineBreak)
        ):
            pass
        elif (
                isinstance(last_token, TokenParagraphBreak)
                and isinstance(token, TokenParagraphBreak)
        ):
            pass
        else:
            result.append(token)

        last_token = token

    # endregion

    # region Remove trailing breaks

    first_non_break = None  # type: Optional[int]
    for i, token in enumerate(reversed(result)):
        if not isinstance(token, (TokenLineBreak, TokenParagraphBreak)):
            first_non_break = i
            break

    if first_non_break is None:
        result = []

    elif first_non_break == 0:
        pass

    else:
        result = result[:-first_non_break]

    # endregion

    return result


class Renderer(
    intermediate_rendering.DocutilsElementTransformer[List[Token]]):
    """Render descriptions as C# docstring XML."""

    # fmt: off
    @ensure(
        lambda result:
        not (result[0] is not None)
        or (
            all(
                '\n' not in token.content
                for token in result[0]
                if isinstance(token, TokenText)
            )))
    # fmt: on
    def transform_text(
            self, element: docutils.nodes.Text
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        return [TokenText(element.astext().replace('\n', ' '))], None

    def transform_symbol_reference_in_doc(
            self, element: intermediate.SymbolReferenceInDoc
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        cls_name = rdf_shacl_naming.class_name(element.symbol.name)
        return [TokenText(f"'{cls_name}'")], None

    def transform_property_reference_in_doc(
            self, element: intermediate.PropertyReferenceInDoc
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        prop_name = rdf_shacl_naming.property_name(Identifier(element.path))
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

            assert child_tokens is not None
            tokens.append(TokenText('* '))
            tokens.extend(child_tokens)

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

    def transform_document(
            self,
            element: docutils.nodes.document
    ) -> Tuple[Optional[List[Token]], Optional[str]]:
        tokens = []  # type: List[Token]
        for child in element:
            child_tokens, error = self.transform(child)
            if error is not None:
                return None, error

            assert child_tokens is not None
            tokens.extend(child_tokens)

        result = without_redundant_breaks(tokens=tokens)
        return result, None


