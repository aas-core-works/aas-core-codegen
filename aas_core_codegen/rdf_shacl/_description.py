"""Render the description of a class or a property as a plain text."""
from typing import Optional, List, Tuple, Sequence, cast, Union

import docutils.nodes
from icontract import ensure

from aas_core_codegen.common import assert_never, assert_union_of_descendants_exhaustive
from aas_core_codegen.intermediate import (
    doc as intermediate_doc,
    rendering as intermediate_rendering,
)
from aas_core_codegen.rdf_shacl import naming as rdf_shacl_naming

# NOTE (mristin, 2022-03-23):
# The representation of the documentation as tokens was definitely a wrong decision.
# However, we do not prioritize descriptions in RDF+SHACL at the moment so we leave out
# the refactoring for now. A better approach would be to first transform
# into a nested structure similar to HTML (paragraph, unordered list, ordered list,
# *etc.*) and then render this nested structure in a separate step.


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


def without_trailing_breaks(tokens: Sequence["TokenUnion"]) -> List["TokenUnion"]:
    """Remove all the trailing breaks at the end of the ``tokens``."""
    result = list(tokens)

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
        result = result[:-first_non_break]  # pylint: disable=invalid-unary-operand-type

    return result


def without_redundant_breaks(tokens: Sequence["TokenUnion"]) -> List["TokenUnion"]:
    """Remove the redundant breaks from ``tokens`` and return a cleaned-up list."""
    if len(tokens) == 0:
        return []

    last_token = None  # type: Optional[TokenUnion]
    result = []  # type: List[TokenUnion]

    # region Remove multiple consecutive paragraph breaks and line breaks

    for token in tokens:
        if last_token is None:
            result.append(token)
        elif isinstance(last_token, TokenLineBreak) and isinstance(
            token, TokenLineBreak
        ):
            pass
        elif isinstance(last_token, TokenParagraphBreak) and isinstance(
            token, TokenParagraphBreak
        ):
            pass
        else:
            result.append(token)

        last_token = token

    # endregion

    result = without_trailing_breaks(tokens=result)

    return result


class Renderer(intermediate_rendering.DocutilsElementTransformer[List["TokenUnion"]]):
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
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        return [TokenText(element.astext().replace("\n", " "))], None

    def transform_symbol_reference_in_doc(
        self, element: intermediate_doc.SymbolReference
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        cls_name = rdf_shacl_naming.class_name(element.symbol.name)
        return [TokenText(f"'{cls_name}'")], None

    def transform_attribute_reference_in_doc(
        self, element: intermediate_doc.AttributeReference
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        if isinstance(element.reference, intermediate_doc.PropertyReference):
            prop_name = rdf_shacl_naming.property_name(element.reference.prop.name)
            return [TokenText(f"'{prop_name}'")], None

        elif isinstance(
            element.reference, intermediate_doc.EnumerationLiteralReference
        ):
            literal_name = rdf_shacl_naming.enumeration_literal(
                element.reference.literal.name
            )

            return [TokenText(f"'{literal_name}'")], None

        else:
            assert_never(element.reference)

    def transform_argument_reference_in_doc(
        self, element: intermediate_doc.ArgumentReference
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        # Argument references are not really meaningful for SHACL, so we just
        # return them as-is.
        return [TokenText(element.reference)], None

    def transform_constraint_reference_in_doc(
        self, element: intermediate_doc.ConstraintReference
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        return [TokenText(f"Constraint {element.reference}")], None

    def transform_literal(
        self, element: docutils.nodes.literal
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        return [TokenText(element.astext())], None

    def transform_paragraph(
        self, element: docutils.nodes.paragraph
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        tokens = []  # type: List["TokenUnion"]
        errors = []  # type: List[str]

        for child in element.children:
            child_tokens, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert child_tokens is not None
                tokens.extend(child_tokens)

        if len(errors) > 0:
            return None, errors

        tokens.append(TokenParagraphBreak())

        return tokens, None

    def transform_emphasis(
        self, element: docutils.nodes.emphasis
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        tokens = []  # type: List["TokenUnion"]
        errors = []  # type: List[str]

        for child in element.children:
            child_tokens, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert child_tokens is not None
                tokens.extend(child_tokens)

        if len(errors) > 0:
            return None, errors

        return tokens, None

    def transform_list_item(
        self, element: docutils.nodes.list_item
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        if len(element.children) != 1 or not isinstance(
            element.children[0], docutils.nodes.paragraph
        ):
            return None, [
                (
                    f"Expected the list item to contain a single child (paragraph), "
                    f"but got: {element}"
                )
            ]

        para_element = element.children[0]

        tokens = []  # type: List["TokenUnion"]

        if len(para_element.children) == 0:
            return [TokenText("* (empty)")], None

        errors = []  # type: List[str]

        for child in para_element.children:
            child_tokens, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert child_tokens is not None
                tokens.append(TokenText("* "))
                tokens.extend(child_tokens)

        if len(errors) > 0:
            return None, errors

        return tokens, None

    def transform_bullet_list(
        self, element: docutils.nodes.bullet_list
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        tokens = []  # type: List["TokenUnion"]
        errors = []  # type: List[str]

        for child in element.children:
            child_tokens, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert child_tokens is not None
                tokens.extend(child_tokens)
                tokens.append(TokenLineBreak())

        if len(errors) > 0:
            return None, errors

        return tokens, None

    def transform_note(
        self, element: docutils.nodes.note
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        tokens = []  # type: List["TokenUnion"]
        errors = []  # type: List[str]

        for child in element.children:
            child_tokens, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert child_tokens is not None
                tokens.extend(child_tokens)

        if len(errors) > 0:
            return None, errors

        tokens = (
            cast(List["TokenUnion"], [TokenText("NOTE:"), TokenLineBreak()]) + tokens
        )

        return tokens, None

    def transform_reference(
        self, element: docutils.nodes.reference
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        tokens = []  # type: List["TokenUnion"]
        errors = []  # type: List[str]

        for child in element.children:
            child_tokens, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert child_tokens is not None
                tokens.extend(child_tokens)
                tokens.append(TokenLineBreak())

        if len(errors) > 0:
            return None, errors

        return tokens, None

    def transform_field_body(
        self, element: docutils.nodes.field_body
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        tokens = []  # type: List[TokenUnion]
        errors = []  # type: List[str]

        for child in element:
            child_tokens, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert child_tokens is not None
                tokens.extend(child_tokens)

        result = without_redundant_breaks(tokens=tokens)
        return result, None

    def transform_document(
        self, element: docutils.nodes.document
    ) -> Tuple[Optional[List["TokenUnion"]], Optional[List[str]]]:
        tokens = []  # type: List[TokenUnion]
        errors = []  # type: List[str]

        for child in element:
            child_tokens, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert child_tokens is not None
                tokens.extend(child_tokens)

        result = without_redundant_breaks(tokens=tokens)
        return result, None


TokenUnion = Union[TokenText, TokenParagraphBreak, TokenLineBreak]
assert_union_of_descendants_exhaustive(union=TokenUnion, base_class=Token)
