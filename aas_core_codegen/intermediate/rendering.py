"""Provide rendering functions for common generation tasks."""
import abc
from typing import TypeVar, Generic, Tuple, Optional, List

import docutils.nodes
from icontract import ensure, DBC

from aas_core_codegen.intermediate import doc

T = TypeVar("T")


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
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Dispatch the transformation to the appropriate ``transform_*``."""
        # NOTE (mristin, 2021-12-26):
        # Please keep the dispatching order. We have to implement a chain-of-command,
        # not an efficient dispatch as classes inherit from each other.

        if isinstance(element, docutils.nodes.Text):
            return self.transform_text(element)

        elif isinstance(element, doc.ReferenceToOurType):
            return self.transform_reference_to_our_type_in_doc(element)

        elif isinstance(element, doc.ReferenceToAttribute):
            return self.transform_reference_to_attribute_in_doc(element)

        elif isinstance(element, doc.ReferenceToArgument):
            return self.transform_reference_to_argument_in_doc(element)

        elif isinstance(element, doc.ReferenceToConstraint):
            return self.transform_reference_to_constraint_in_doc(element)

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

        elif isinstance(element, docutils.nodes.field_body):
            return self.transform_field_body(element)

        elif isinstance(element, docutils.nodes.document):
            return self.transform_document(element)

        else:
            return None, [
                (
                    f"Handling of the element of a description "
                    f"with type {type(element)} "
                    f"has not been implemented: {element}"
                )
            ]

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_text(
        self, element: docutils.nodes.Text
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a text element into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_reference_to_our_type_in_doc(
        self, element: doc.ReferenceToOurType
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a reference to our type into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_reference_to_attribute_in_doc(
        self, element: doc.ReferenceToAttribute
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a reference to an attribute into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_reference_to_argument_in_doc(
        self, element: doc.ReferenceToArgument
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a reference to an argument into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_reference_to_constraint_in_doc(
        self, element: doc.ReferenceToConstraint
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a reference to a constraint into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_literal(
        self, element: docutils.nodes.literal
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a code literal into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_paragraph(
        self, element: docutils.nodes.paragraph
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a paragraph element into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_emphasis(
        self, element: docutils.nodes.emphasis
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform an emphasis element into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_list_item(
        self, element: docutils.nodes.list_item
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a list item element into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_bullet_list(
        self, element: docutils.nodes.bullet_list
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a bullet list element into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_note(
        self, element: docutils.nodes.note
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a note element into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_reference(
        self, element: docutils.nodes.reference
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a general reference element into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_field_body(
        self, element: docutils.nodes.field_body
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a field body into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_document(
        self, element: docutils.nodes.document
    ) -> Tuple[Optional[T], Optional[List[str]]]:
        """Transform a document into something."""
        raise NotImplementedError()
