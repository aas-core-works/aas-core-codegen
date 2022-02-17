"""Generate RDF and SHACL identifiers based on the identifiers from the meta-model."""
from typing import List

from aas_core_codegen.common import Identifier, Stripped
from aas_core_codegen import naming


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate the class name from the intermediate class ``identifier``.

    >>> class_name(Identifier("something"))
    'Something'

    >>> class_name(Identifier("something_to_URL"))
    'SomethingToURL'
    """
    parts = identifier.split("_")

    cased = []  # type: List[str]
    for part in parts:
        if part in naming.UPPERCASE_ABBREVIATION_SET:
            cased.append(part.upper())
        else:
            cased.append(part.capitalize())

    return Identifier("".join(cased))


_LOWERCASE_WORDS_IN_LABEL = {"to", "in"}


def class_label(identifier: Identifier) -> Stripped:
    """
    Generate the class label from the intermediate class ``identifier``.

    >>> class_label(Identifier("something"))
    'Something'

    >>> class_label(Identifier("something_good_to_URL"))
    'Something Good to URL'
    """
    parts = identifier.split("_")

    cased = []  # type: List[str]
    for part in parts:
        if part in naming.UPPERCASE_ABBREVIATION_SET:
            cased.append(part.upper())
        elif part in _LOWERCASE_WORDS_IN_LABEL:
            cased.append(part.lower())
        else:
            cased.append(part.capitalize())

    return Stripped(" ".join(cased))


def property_name(identifier: Identifier) -> Identifier:
    """
    Generate a property name based on its meta-model ``identifier``.

    >>> property_name(Identifier("something"))
    'something'

    >>> property_name(Identifier("something_to_URL"))
    'somethingToURL'
    """
    parts = identifier.split("_")

    cased = []  # type: List[str]
    for i, part in enumerate(parts):
        if i == 0:
            cased.append(part.lower())
        else:
            if part in naming.UPPERCASE_ABBREVIATION_SET:
                cased.append(part.upper())
            else:
                cased.append(part.capitalize())

    return Identifier("".join(cased))


def property_label(identifier: Identifier) -> Stripped:
    """
    Generate the property label from the intermediate class ``identifier``.

    >>> property_label(Identifier("something"))
    'something'

    >>> property_label(Identifier("something_good_to_URL"))
    'something good to URL'
    """
    parts = identifier.split("_")

    cased = []  # type: List[str]
    for part in parts:
        if part in naming.UPPERCASE_ABBREVIATION_SET:
            cased.append(part.upper())
        else:
            cased.append(part.lower())

    return Stripped(" ".join(cased))


def enumeration_literal(identifier: Identifier) -> Stripped:
    """
    Generate the enumeration literal for its intermediate ``identifier``.

    >>> enumeration_literal(Identifier('something'))
    'Something'

    >>> enumeration_literal(Identifier("something_to_URL"))
    'SomethingToUrl'
    """
    parts = identifier.split("_")
    return Stripped("".join(part.capitalize() for part in parts))


def enumeration_literal_label(identifier: Identifier) -> Stripped:
    """
    Generate the label for an enumeration literal with intermediate ``identifier``.

    >>> enumeration_literal_label(Identifier("something"))
    'Something'

    >>> enumeration_literal_label(Identifier("something_good_to_URL"))
    'Something Good to URL'
    """
    parts = identifier.split("_")

    cased = []  # type: List[str]
    for part in parts:
        if part in naming.UPPERCASE_ABBREVIATION_SET:
            cased.append(part.upper())
        elif part in _LOWERCASE_WORDS_IN_LABEL:
            cased.append(part.lower())
        else:
            cased.append(part.capitalize())

    return Stripped(" ".join(cased))
