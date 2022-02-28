"""Provide types for the references in the docstrings."""

# pylint: disable=keyword-arg-before-vararg

from typing import Union

import docutils
import docutils.nodes
from icontract import require

from aas_core_codegen.intermediate._types import (
    Symbol,
    Property,
    Enumeration,
    EnumerationLiteral,
    ClassUnion,
)


class SymbolReference(
    docutils.nodes.Inline, docutils.nodes.TextElement  # type: ignore
):
    """Represent a reference in the documentation to a symbol in the symbol table."""

    def __init__(  # type: ignore
        self,
        symbol: Symbol,
        rawsource="",
        text="",
        *children,
        **attributes,
    ) -> None:
        """Initialize with the given symbol and propagate the rest to the parent."""
        self.symbol = symbol
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes
        )


class PropertyReference:
    """Model a reference to a property, usually used in the docstrings."""

    @require(lambda cls, prop: id(prop) in cls.property_id_set)
    def __init__(self, cls: ClassUnion, prop: Property) -> None:
        self.cls = cls
        self.prop = prop


class EnumerationLiteralReference:
    """Model a reference to an enumeration literal, usually used in the docstrings."""

    @require(lambda symbol, literal: id(literal) in symbol.literal_id_set)
    def __init__(self, symbol: Enumeration, literal: EnumerationLiteral) -> None:
        self.symbol = symbol
        self.literal = literal


class AttributeReference(
    docutils.nodes.Inline, docutils.nodes.TextElement  # type: ignore
):
    """
    Represent a reference in the documentation to an "attribute".

    The attribute, in this context, refers to the role ``:attr:``. The references
    implies either a reference to a property of a class or a literal of an enumeration.
    """

    def __init__(  # type: ignore
        self,
        reference: Union[PropertyReference, EnumerationLiteralReference],
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


class ArgumentReference(
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


class ConstraintReference(
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
