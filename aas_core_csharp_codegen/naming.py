from aas_core_csharp_codegen.common import Identifier


def json_property(identifier: Identifier) -> Identifier:
    """
    Generate a JSON name of a property based on its meta-model ``identifier``.

    >>> json_property(Identifier("something"))
    'something'

    >>> json_property(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    return Identifier(
        "{}{}".format(
            parts[0].lower(),
            ''.join(part.capitalize() for part in parts[1:])))


def json_model_type(identifier: Identifier) -> Identifier:
    """
    Generate the ``modelType`` of the class based on its meta-model ``identifier``.

    >>> json_model_type(Identifier("something"))
    'Something'

    >>> json_model_type(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    parts = identifier.split('_')

    return Identifier("{}".format(''.join(part.capitalize() for part in parts)))


def xml_name(identifier: Identifier) -> Identifier:
    """
    Generate the XML tag name for the given entity based on its ``identifier``.

    >>> xml_name(Identifier("something"))
    'something'

    >>> xml_name(Identifier("URL_to_something"))
    'urlToSomething'
    """
    parts = identifier.split('_')
    assert len(parts) >= 1, (
        f"Expected at least one part for the valid identifier: {identifier}")

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    return Identifier("{}{}".format(
        parts[0].lower(), ''.join(part.capitalize() for part in parts[1:])))


def xml_attribute(identifier: Identifier) -> Identifier:
    """
    Generate the XML attribute name for the given property based on its ``identifier``.

    >>> xml_attribute(Identifier("something"))
    'something'

    >>> xml_attribute(Identifier("URL_to_something"))
    'urlToSomething'
    """
    parts = identifier.split('_')
    assert len(parts) >= 1, (
        f"Expected at least one part for the valid identifier: {identifier}")

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    return Identifier("{}{}".format(
        parts[0].lower(), ''.join(part.capitalize() for part in parts[1:])))
