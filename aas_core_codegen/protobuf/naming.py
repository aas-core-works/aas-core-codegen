"""Generate ProtoBuf identifiers based on the identifiers from the meta-model."""

from typing import Union

import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier, assert_never


def interface_name(identifier: Identifier) -> Identifier:
    raise NotImplementedError("Interfaces are not supported by proto3.")


def enum_name(identifier: Identifier) -> Identifier:
    """
    Generate a ProtoBuf name for an enum based on its meta-model ``identifier``.

    >>> enum_name(Identifier("something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def enum_literal_name(identifier: Identifier) -> Identifier:
    """
    Generate a Protobuf name for an enum literal based on its meta-model ``identifier``.

    >>> enum_literal_name(Identifier("something"))
    'SOMETHING'

    >>> enum_literal_name(Identifier("URL_to_something"))
    'URL_TO_SOMETHING'
    """
    return aas_core_codegen.naming.upper_snake_case(identifier)


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate a ProtoBuf name for a class based on its meta-model ``identifier``.

    >>> class_name(Identifier("something"))
    'Something'

    >>> class_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def name_of(
    something: Union[
        intermediate.Enumeration, intermediate.ConcreteClass, intermediate.Interface
    ]
) -> Identifier:
    """Dispatch to the appropriate naming function."""
    if isinstance(something, intermediate.Enumeration):
        return enum_name(something.name)

    elif isinstance(something, intermediate.ConcreteClass):
        return class_name(something.name)

    elif isinstance(something, intermediate.Interface):
        return interface_name(something.name)

    else:
        assert_never(something)

    raise AssertionError("Should not have gotten here")


def property_name(identifier: Identifier) -> Identifier:
    """
    Generate a ProtoBuf name for a public property based on its meta-model ``identifier``.

    >>> property_name(Identifier("something"))
    'something'

    >>> property_name(Identifier("something_to_URL"))
    'something_to_url'
    """
    return aas_core_codegen.naming.lower_snake_case(identifier)


def private_property_name(identifier: Identifier) -> Identifier:
    raise NotImplementedError(
        "Private properties are not supported by proto3 Messages."
    )


def private_method_name(identifier: Identifier) -> Identifier:
    raise NotImplementedError("Methods are not supported by proto3 Messages.")


def method_name(identifier: Identifier) -> Identifier:
    raise NotImplementedError("Methods are not supported by proto3 Messages.")


def argument_name(identifier: Identifier) -> Identifier:
    raise NotImplementedError("Arguments are not supported by proto3 Messages.")


def variable_name(identifier: Identifier) -> Identifier:
    raise NotImplementedError("Variables are not supported by proto3 Messages.")
