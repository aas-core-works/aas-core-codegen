"""Generate C# identifiers based on the identifiers from the meta-model."""

from aas_core_csharp_codegen.common import Identifier


def interface_name(identifier: Identifier) -> Identifier:
    """
    Generate a C# interface name based on its meta-model ``identifier``.

    >>> interface_name(Identifier("something"))
    'ISomething'

    >>> interface_name(Identifier("URL_to_something"))
    'IUrlToSomething'
    """
    parts = identifier.split('_')

    return Identifier("I{}".format(''.join(part.capitalize() for part in parts)))


def enum_name(identifier: Identifier) -> Identifier:
    """
    Generate a C# name for an enum based on its meta-model ``identifier``.

    >>> enum_name(Identifier("something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    parts = identifier.split('_')

    return Identifier("{}".format(''.join(part.capitalize() for part in parts)))


def enum_literal_name(identifier: Identifier) -> Identifier:
    """
    Generate a C# name for an enum literal based on its meta-model ``identifier``.

    >>> enum_literal_name(Identifier("something"))
    'Something'

    >>> enum_literal_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    parts = identifier.split('_')

    return Identifier("{}".format(''.join(part.capitalize() for part in parts)))


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate a C# name for a class based on its meta-model ``identifier``.

    >>> enum_name(Identifier("something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    parts = identifier.split('_')

    return Identifier("{}".format(''.join(part.capitalize() for part in parts)))


def private_property(identifier: Identifier) -> Identifier:
    """
    Generate a C# name for a private property based on its meta-model ``identifier``.

    >>> private_property(Identifier("something"))
    '_something'

    >>> private_property(Identifier("something_to_URL"))
    '_somethingToUrl'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier("_{}".format(parts[0].lower()))

    return Identifier(
        "_{}{}".format(parts[0], ''.join(part.capitalize() for part in parts[1:])))


def getter_name(identifier: Identifier) -> Identifier:
    """
    Generate a C# name for a getter based on the ``identifier`` of a property.

    >>> getter_name(Identifier("something"))
    'something'

    >>> getter_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    return Identifier(
        "{}{}".format(parts[0], ''.join(part.capitalize() for part in parts[1:])))


def setter_name(identifier: Identifier) -> Identifier:
    """
    Generate a C# name for a setter based on the ``identifier`` of a property.

    >>> setter_name(Identifier("something"))
    'setSomething'

    >>> setter_name(Identifier("something_to_URL"))
    'setSomethingToUrl'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier("set{}".format(parts[0].capitalize()))

    return Identifier(
        "set{}".format(''.join(part.capitalize() for part in parts)))
