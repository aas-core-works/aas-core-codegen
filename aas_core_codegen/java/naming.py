"""Generate Java identifiers based on the identifiers from the meta-model."""
from typing import Union

import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier, assert_never


def interface_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java interface name based on its meta-model ``identifier``.

    >>> interface_name(Identifier("something"))
    'ISomething'

    >>> interface_name(Identifier("URL_to_something"))
    'IUrlToSomething'
    """
    return Identifier(f"I{aas_core_codegen.naming.capitalized_camel_case(identifier)}")


def enum_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for an enum based on its meta-model ``identifier``.

    >>> enum_name(Identifier("something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def enum_literal_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for an enum literal based on its meta-model ``identifier``.

    >>> enum_literal_name(Identifier("something"))
    'SOMETHING'

    >>> enum_literal_name(Identifier("URL_to_something"))
    'URL_TO_SOMETHING'
    """
    return aas_core_codegen.naming.upper_pascal_case(identifier)


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for a class based on its meta-model ``identifier``.

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
    Generate a Java name for a public property based on its meta-model ``identifier``.

    >>> property_name(Identifier("something"))
    'something'

    >>> property_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def private_property_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for a private property based on the ``identifier``.

    >>> private_property_name(Identifier("something"))
    'something'

    >>> private_property_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def private_method_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for a private method based on the ``identifier``.

    >>> private_method_name(Identifier("do_something"))
    'doSomething'

    >>> private_method_name(Identifier("do_something_to_URL"))
    'doSomethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def method_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for a member method based on its meta-model ``identifier``.

    >>> method_name(Identifier("do_something"))
    'doSomething'

    >>> method_name(Identifier("do_something_to_URL"))
    'doSomethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def argument_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for an argument based on its meta-model ``identifier``.

    >>> argument_name(Identifier("something"))
    'something'

    >>> argument_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def variable_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for a variable based on its meta-model ``identifier``.

    >>> variable_name(Identifier("something"))
    'something'

    >>> variable_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def getter_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for a getter on its meta-model ``identifier``.

    >>> getter_name(Identifier("something"))
    'getSomething'

    >>> getter_name(Identifier("something_to_URL"))
    'getSomethingToUrl'
    """
    return Identifier(
        f"get{aas_core_codegen.naming.capitalized_camel_case(identifier)}"
    )


def setter_name(identifier: Identifier) -> Identifier:
    """
    Generate a Java name for a setter on its meta-model ``identifier``.

    >>> setter_name(Identifier("something"))
    'setSomething'

    >>> setter_name(Identifier("something_to_URL"))
    'setSomethingToUrl'
    """
    return Identifier(
        f"set{aas_core_codegen.naming.capitalized_camel_case(identifier)}"
    )
