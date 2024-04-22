"""Generate RDF and SHACL identifiers based on the identifiers from the meta-model."""

from typing import List

from icontract import require

from aas_core_codegen import naming
from aas_core_codegen.common import Identifier, Stripped

_LOWERCASE_WORDS_IN_LABEL = {"to", "in"}


def _capitalized_label(identifier: Identifier) -> Stripped:
    """
    Generate the label starting with a capital letter.

    >>> _capitalized_label(Identifier("Something"))
    'Something'

    >>> _capitalized_label(Identifier("Something_good_to_URL"))
    'Something Good to URL'

    >>> _capitalized_label(Identifier("URL_to_something"))
    'URL to Something'
    """
    parts = identifier.split("_")

    cased = []  # type: List[str]
    for part in parts:
        if part in _LOWERCASE_WORDS_IN_LABEL:
            cased.append(part.lower())
        else:
            if part == part.lower():
                cased.append(part.capitalize())
            else:
                cased.append(part)

    return Stripped(" ".join(cased))


# fmt: off
@require(
    lambda identifier: identifier[0].isupper(),
    "The class name must start with a capital letter"
)
# fmt: on
def class_name(identifier: Identifier) -> Identifier:
    """
    Generate the class name from the intermediate class ``identifier``.

    >>> class_name(Identifier("Something"))
    'Something'

    >>> class_name(Identifier("Something_to_URL"))
    'SomethingToUrl'

    >>> class_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return naming.capitalized_camel_case(identifier)


# fmt: off
@require(
    lambda identifier: identifier[0].isupper(),
    "The class name must start with a capital letter"
)
# fmt: on
def class_label(identifier: Identifier) -> Stripped:
    """
    Generate the class label from the intermediate class ``identifier``.

    >>> class_label(Identifier("Something"))
    'Something'

    >>> class_label(Identifier("Something_good_to_URL"))
    'Something Good to URL'

    >>> class_label(Identifier("URL_to_something"))
    'URL to Something'
    """
    return _capitalized_label(identifier)


def property_name(identifier: Identifier) -> Identifier:
    """
    Generate a property name based on its meta-model ``identifier``.

    >>> property_name(Identifier("something"))
    'something'

    >>> property_name(Identifier("something_to_URL"))
    'somethingToUrl'

    >>> property_name(Identifier("URL_to_something"))
    'urlToSomething'
    """
    return naming.lower_camel_case(identifier)


def property_label(identifier: Identifier) -> Stripped:
    """
    Generate the property label from the intermediate class ``identifier``.

    >>> property_label(Identifier("something"))
    'something'

    >>> property_label(Identifier("something_good_to_URL"))
    'something good to URL'

    >>> property_label(Identifier("URL_to_something"))
    'URL to something'
    """
    return Stripped(" ".join(identifier.split("_")))


def enumeration_literal(identifier: Identifier) -> Stripped:
    """
    Generate the enumeration literal for its intermediate ``identifier``.

    >>> enumeration_literal(Identifier('something'))
    'Something'

    >>> enumeration_literal(Identifier("something_to_URL"))
    'SomethingToUrl'

    >>> enumeration_literal(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return naming.capitalized_camel_case(identifier)


def enumeration_literal_label(identifier: Identifier) -> Stripped:
    """
    Generate the label for an enumeration literal with intermediate ``identifier``.

    >>> enumeration_literal_label(Identifier("something"))
    'Something'

    >>> enumeration_literal_label(Identifier("something_good_to_URL"))
    'Something Good to URL'

    >>> enumeration_literal_label(Identifier("URL_to_something_good"))
    'URL to Something Good'
    """
    return _capitalized_label(identifier)
