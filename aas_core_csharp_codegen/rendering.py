"""Provide rendering functions for common generation tasks."""
from typing import TypeVar, Generic, Tuple, Optional

import docutils.nodes
from icontract import ensure

from aas_core_csharp_codegen import intermediate


def indent_but_first_line(text: str, indention: str) -> str:
    """
    Indent all but the first of the given ``text`` by ``indention``.

    For example, this helps you insert indented blocks into formatted string literals.
    """
    return "\n".join(
        indention + line if i > 0 else line
        for i, line in enumerate(text.splitlines())
    )


T = TypeVar('T')


class DocutilsElementTransformer(Generic[T]):
    """
    Transform a pre-defined subset of the docutils elements.

    The subset is limited to the elements which we expect in the docstrings of
    our meta-model. Following YAGNI ("you ain't gonna need it"), we do not visit
    all the possible elements as our docstrings are indeed limited in style.

    All the transforming functions return either a result or an error.
    """

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform(
            self, element: docutils.nodes.Element
    ) -> Tuple[Optional[T], Optional[str]]:
        if isinstance(element, docutils.nodes.Text):
            return self.transform_text(element)

        # TODO: continue here: rewrite this, then refactor the csharp part, then implement RDF
        elif isinstance(element, intermediate.SymbolReferenceInDoc):
            return self
            cls_name = rdf_shacl_naming.class_name(element.symbol.name)
            return [_DescriptionTokenText(f"'{cls_name}'")], None

        elif isinstance(element, intermediate.PropertyReferenceInDoc):
            prop_name = rdf_shacl_naming.property_name(
                Identifier(element.property_name))
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
                    [_DescriptionTokenText("* (empty)"), _DescriptionTokenLineBreak],
                    None
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
