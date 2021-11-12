"""Generate RDF and SHACL identifiers based on the identifiers from the meta-model."""
from typing import List

from aas_core_csharp_codegen.common import Identifier, Stripped


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate the class name from the intermediate class ``identifier``.

    >>> class_name(Identifier("something"))
    'Something'

    >>> class_name(Identifier("something_to_URL"))
    'SomethingToUrl'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier(parts[0].capitalize())

    return Identifier(
        "{}{}".format(
            parts[0].capitalize(),
            ''.join(part.capitalize() for part in parts[1:])))


_UPPERCASE_ABBREVIATION_SET = {
    "URL",
    "ID"
}

_LOWERCASE_WORDS_IN_LABEL = {
    "to",
    "in"
}


def class_label(identifier: Identifier) -> Stripped:
    """
    Generate the class label from the intermediate class ``identifier``.

    >>> class_label(Identifier("something"))
    'Something'

    >>> class_label(Identifier("something_good_to_URL"))
    'Something Good to URL'
    """
    parts = identifier.split('_')

    cased = []  # type: List[str]
    for part in parts:
        if part in _UPPERCASE_ABBREVIATION_SET:
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
    'somethingToUrl'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    return Identifier(
        "{}{}".format(
            parts[0].lower(),
            ''.join(part.capitalize() for part in parts[1:])))


def property_label(identifier: Identifier) -> Stripped:
    """
    Generate the property label from the intermediate class ``identifier``.

    >>> property_label(Identifier("something"))
    'something'

    >>> property_label(Identifier("something_good_to_URL"))
    'something good to URL'
    """
    parts = identifier.split('_')

    cased = []  # type: List[str]
    for part in parts:
        if part in _UPPERCASE_ABBREVIATION_SET:
            cased.append(part.upper())
        else:
            cased.append(part.lower())

    return Stripped(" ".join(cased))

def enumeration_literal(identifier: Identifier) -> Stripped:
    """
    Generate the enumeration literal for its intermediate ``identifier``.

    >>> enumeration_literal(Identifier())
    """
    # TODO: continue here, implement the doctests and then go back to rdf
