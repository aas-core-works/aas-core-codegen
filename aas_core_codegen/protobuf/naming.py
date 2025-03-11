"""Generate ProtoBuf identifiers based on the identifiers from the meta-model."""

from typing import Union

from icontract import ensure

import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier, assert_never


def interface_name(identifier: Identifier) -> Identifier:
    """
    Generate a ProtoBuf name for an interface based on its meta-model ``identifier``.

    Since proto3 does not directly support interfaces, but only one-of messages
    (commonly suffixed "_choice"), these names are generated here.
    """
    return Identifier(
        aas_core_codegen.naming.capitalized_camel_case(identifier) + "_choice"
    )


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
    """
    Generate a ProtoBuf name for a private property.

    This method is not to be used because proto3 does not support private properties.
    """
    raise NotImplementedError(
        "Private properties are not supported by proto3 Messages."
    )


def private_method_name(identifier: Identifier) -> Identifier:
    """
    Generate a ProtoBuf name for a private method.

    This method is not to be used because proto3 does not support private methods.
    """
    raise NotImplementedError("Methods are not supported by proto3 Messages.")


def method_name(identifier: Identifier) -> Identifier:
    """
    Generate a ProtoBuf name for a method.

    This method is not to be used because proto3 does not support methods.
    """
    raise NotImplementedError("Methods are not supported by proto3 Messages.")


def argument_name(identifier: Identifier) -> Identifier:
    """
    Generate a ProtoBuf name for an argument.

    This method is not to be used because proto3 does not support methods and
    thus no arguments.
    """
    raise NotImplementedError("Arguments are not supported by proto3 Messages.")


def variable_name(identifier: Identifier) -> Identifier:
    """
    Generate a ProtoBuf name for a variable.

    This method is not to be used because proto3 does not support variables.
    """
    raise NotImplementedError("Variables are not supported by proto3 Messages.")
