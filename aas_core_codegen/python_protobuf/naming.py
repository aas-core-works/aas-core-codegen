"""Emulate naming logic for our types to Protocol Buffers in Python code."""

from aas_core_codegen.common import Identifier
from aas_core_codegen import naming


def enum_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an enum based on its meta-model ``identifier``.

    >>> enum_name(Identifier("something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return naming.capitalized_camel_case(identifier)


def enum_literal_constant_name(
    enumeration_name: Identifier, literal_name: Identifier
) -> Identifier:
    """
    Generate a constant identifier for an enum literal in the meta-model.

    >>> enum_literal_constant_name(
    ...     Identifier("that"), Identifier("literal")
    ... )
    'That_LITERAL'

    >>> enum_literal_constant_name(
    ...     Identifier("URL_to_something"), Identifier("ABC_shines")
    ... )
    'Urltosomething_ABC_SHINES'

    >>> enum_literal_constant_name(
    ...     Identifier("Modelling_kind"), Identifier("Template")
    ... )
    'Modellingkind_TEMPLATE'
    """
    enum_name_joined = "".join(enumeration_name.split("_"))

    return Identifier(f"{enum_name_joined.capitalize()}_{literal_name.upper()}")


def property_name(identifier: Identifier) -> Identifier:
    """
    Generate the name of the property in a Protocol Buffer generated class.

    >>> property_name(Identifier("something"))
    'something'

    >>> property_name(Identifier("something_to_URL"))
    'something_to_url'

    >>> property_name(Identifier("URL_to_something"))
    'url_to_something'
    """
    return naming.lower_snake_case(identifier)


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a class based on its meta-model ``identifier``.

    >>> class_name(Identifier("something"))
    'Something'

    >>> class_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return naming.capitalized_camel_case(identifier)


def choice_class_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a choice (union) class based on its meta-model ``identifier``.

    >>> choice_class_name(Identifier("something"))
    'Something_choice'

    >>> choice_class_name(Identifier("URL_to_something"))
    'UrlToSomething_choice'
    """
    return Identifier(naming.capitalized_camel_case(identifier) + "_choice")
