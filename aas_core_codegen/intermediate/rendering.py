"""Provide rendering functions for common generation tasks."""
import abc
from typing import TypeVar, Generic, Tuple, Optional

import docutils.nodes
from icontract import ensure, DBC

from aas_core_codegen.intermediate._types import (
    SymbolReferenceInDoc, AttributeReferenceInDoc
)

T = TypeVar('T')


class DocutilsElementTransformer(Generic[T], DBC):
    """
    Transform a pre-defined subset of the docutils elements.

    The subset is limited to the elements which we expect in the docstrings of
    our meta-model. Following YAGNI ("you ain't gonna need it"), we do not visit
    all the possible elements as our docstrings are indeed limited in style.

    Following a common pattern throughout this code base, all the transforming functions
    return either a result or an error.
    """

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform(
            self, element: docutils.nodes.Element
    ) -> Tuple[Optional[T], Optional[str]]:
        if isinstance(element, docutils.nodes.Text):
            return self.transform_text(element)

        elif isinstance(element, SymbolReferenceInDoc):
            return self.transform_symbol_reference_in_doc(element)

        elif isinstance(element, AttributeReferenceInDoc):
            return self.transform_attribute_reference_in_doc(element)

        elif isinstance(element, docutils.nodes.literal):
            return self.transform_literal(element)

        elif isinstance(element, docutils.nodes.paragraph):
            return self.transform_paragraph(element)

        elif isinstance(element, docutils.nodes.emphasis):
            return self.transform_emphasis(element)

        elif isinstance(element, docutils.nodes.list_item):
            return self.transform_list_item(element)

        elif isinstance(element, docutils.nodes.bullet_list):
            return self.transform_bullet_list(element)

        elif isinstance(element, docutils.nodes.note):
            return self.transform_note(element)

        elif isinstance(element, docutils.nodes.reference):
            return self.transform_reference(element)

        elif isinstance(element, docutils.nodes.document):
            return self.transform_document(element)

        else:
            return None, (
                f"Handling of the element of a description with type {type(element)} "
                f"has not been implemented: {element}"
            )

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_text(
            self, element: docutils.nodes.Text
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_symbol_reference_in_doc(
            self, element: SymbolReferenceInDoc
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_attribute_reference_in_doc(
            self, element: AttributeReferenceInDoc
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_literal(
            self, element: docutils.nodes.literal
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_paragraph(
            self, element: docutils.nodes.paragraph
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_emphasis(
            self, element: docutils.nodes.emphasis
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_list_item(
            self, element: docutils.nodes.list_item
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_bullet_list(
            self, element: docutils.nodes.bullet_list
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_note(
            self, element: docutils.nodes.note
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_reference(
            self, element: docutils.nodes.reference
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_document(
            self, element: docutils.nodes.document
    ) -> Tuple[Optional[T], Optional[str]]:
        raise NotImplementedError()
