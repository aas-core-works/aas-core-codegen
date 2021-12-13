"""
Generate identifiers internal to an XML Schema Definition (XSD).

The identifiers are based on the meta-model. Unlike
:py:mod:`aas_core_codegen.naming`, which are used with different generators,
these identifiers are used only for the XSD.
"""
from aas_core_codegen.common import Identifier


def interface_abstract(identifier: Identifier) -> Identifier:
    """
    Generate the identifier for an abstract definition of an interface.

    >>> interface_abstract(Identifier("Something"))
    'something_abstract'

    >>> interface_abstract(Identifier("Something_to_URL"))
    'somethingToUrl_abstract'
    """
    parts = identifier.split("_")
    assert (
        len(parts) >= 1
    ), f"Expected at least one part for the valid identifier: {identifier}"

    if len(parts) == 1:
        return Identifier(f"{parts[0].lower()}_abstract")

    return Identifier(
        "{}{}_abstract".format(
            parts[0].lower(), "".join(part.capitalize() for part in parts[1:])
        )
    )


def model_type(identifier: Identifier) -> Identifier:
    """
    Generate the XML type name for the given class based on its ``identifier``.

    >>> model_type(Identifier("something"))
    'something_t'

    >>> model_type(Identifier("URL_to_something"))
    'urlToSomething_t'
    """
    parts = identifier.split("_")
    assert (
        len(parts) >= 1
    ), f"Expected at least one part for the valid identifier: {identifier}"

    if len(parts) == 1:
        return Identifier(f"{parts[0].lower()}_t")

    return Identifier(
        "{}{}_t".format(
            parts[0].lower(), "".join(part.capitalize() for part in parts[1:])
        )
    )
