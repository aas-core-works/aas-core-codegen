"""Provide types for the references in the docstrings."""

# pylint: disable=keyword-arg-before-vararg

from typing import Union

import docutils
import docutils.nodes
from icontract import require

from aas_core_codegen.intermediate._types import (
    OurType,
    Property,
    Enumeration,
    EnumerationLiteral,
    ClassUnion,
)


class ReferenceToOurType(
    docutils.nodes.Inline, docutils.nodes.TextElement  # type: ignore
):
    """Represent a reference in the documentation to our type."""

    def __init__(  # type: ignore
        self,
        our_type: OurType,
        rawsource="",
        text="",
        *children,
        **attributes,
    ) -> None:
        """Initialize with the given our type and propagate the rest to the parent."""
        self.our_type = our_type
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes
        )


class ReferenceToProperty:
    """Model a reference to a property, usually used in the docstrings."""

    @require(lambda cls, prop: id(prop) in cls.property_id_set)
    def __init__(self, cls: ClassUnion, prop: Property) -> None:
        self.cls = cls
        self.prop = prop


class ReferenceToEnumerationLiteral:
    """Model a reference to an enumeration literal, usually used in the docstrings."""

    @require(lambda enumeration, literal: id(literal) in enumeration.literal_id_set)
    def __init__(self, enumeration: Enumeration, literal: EnumerationLiteral) -> None:
        self.enumeration = enumeration
        self.literal = literal


class ReferenceToAttribute(
    docutils.nodes.Inline, docutils.nodes.TextElement  # type: ignore
):
    """
    Represent a reference in the documentation to an "attribute".

    The attribute, in this context, refers to the role ``:attr:``. The references
    imply either a reference to a property of a class or a literal of an enumeration.
    """

    def __init__(  # type: ignore
        self,
        reference: Union[ReferenceToProperty, ReferenceToEnumerationLiteral],
        rawsource="",
        text="",
        *children,
        **attributes,
    ) -> None:
        """Initialize with ``property_name`` and propagate the rest to the parent."""
        self.reference = reference
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes
        )


class ReferenceToArgument(
    docutils.nodes.Inline, docutils.nodes.TextElement  # type: ignore
):
    """
    Represent a reference in the documentation to a method argument ("parameter").

    The argument, in this context, refers to the role ``:paramref:``.
    """

    def __init__(  # type: ignore
        self,
        reference: str,
        rawsource="",
        text="",
        *children,
        **attributes,
    ) -> None:
        """Initialize with ``reference`` and propagate the rest to the parent."""
        self.reference = reference
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes
        )


class ReferenceToConstraint(
    docutils.nodes.Inline, docutils.nodes.TextElement  # type: ignore
):
    """Represent a reference in the documentation to a constraint."""

    def __init__(  # type: ignore
        self,
        reference: str,
        rawsource="",
        text="",
        *children,
        **attributes,
    ) -> None:
        """Initialize with ``reference`` and propagate the rest to the parent."""
        self.reference = reference
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes
        )
