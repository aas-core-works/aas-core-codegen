"""Generate TypeScript identifiers based on the identifiers from the meta-model."""
from typing import Union

from icontract import require

import aas_core_codegen.naming
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier, assert_never


def name_of(
    something: Union[
        intermediate.Enumeration, intermediate.AbstractClass, intermediate.ConcreteClass
    ]
) -> Identifier:
    """Dispatch the name based on the run-time type of ``something``."""
    if isinstance(something, intermediate.Enumeration):
        return enum_name(something.name)

    elif isinstance(
        something, (intermediate.AbstractClass, intermediate.ConcreteClass)
    ):
        return class_name(something.name)

    else:
        assert_never(something)
        raise AssertionError("Unexpected execution path")  # for mypy


# fmt: off
@require(
    lambda identifier: identifier[0].isupper(),
    "Enumeration name must start with a capital letter"
)
# fmt: on
def enum_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an enum based on its meta-model ``identifier``.

    >>> enum_name(Identifier("Something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'UrlToSomething'

    >>> enum_name(Identifier("Something_to_URL"))
    'SomethingToUrl'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def enum_literal_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an enum literal based on its meta-model ``identifier``.

    >>> enum_literal_name(Identifier("something"))
    'Something'

    >>> enum_literal_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


def constant_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a constant based on its meta-model ``identifier``.

    >>> constant_name(Identifier("something"))
    'SOMETHING'

    >>> constant_name(Identifier("URL_to_something"))
    'URL_TO_SOMETHING'
    """
    parts = identifier.split("_")
    return Identifier("_".join(part.upper() for part in parts))


# fmt: off
@require(
    lambda identifier:
    identifier[0].isupper(),
    "Class names must start with a capital letter"
)
# fmt: on
def class_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a class based on its meta-model ``identifier``.

    >>> class_name(Identifier("Something"))
    'Something'

    >>> class_name(Identifier("URL_to_something"))
    'UrlToSomething'

    >>> class_name(Identifier("Something_to_URL"))
    'SomethingToUrl'
    """
    return aas_core_codegen.naming.capitalized_camel_case(identifier)


# fmt: off
@require(
    lambda identifier:
    identifier[0].isupper(),
    "Interface names must start with a capital letter"
)
# fmt: on
def interface_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a class based on its meta-model ``identifier``.

    >>> interface_name(Identifier("Something"))
    'ISomething'

    >>> interface_name(Identifier("URL_to_something"))
    'IUrlToSomething'

    >>> interface_name(Identifier("Something_to_URL"))
    'ISomethingToUrl'
    """
    return Identifier(f"I{aas_core_codegen.naming.capitalized_camel_case(identifier)}")


def property_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a public property based on its meta-model ``identifier``.

    >>> property_name(Identifier("something"))
    'something'

    >>> property_name(Identifier("something_to_URL"))
    'somethingToUrl'

    >>> property_name(Identifier("URL_to_something"))
    'urlToSomething'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def function_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a function from its meta-model ``identifier``.

    >>> function_name(Identifier("do_something"))
    'doSomething'

    >>> function_name(Identifier("do_something_to_URL"))
    'doSomethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def method_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an instance method based on its meta-model ``identifier``.

    >>> method_name(Identifier("do_something"))
    'doSomething'

    >>> method_name(Identifier("do_something_to_URL"))
    'doSomethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def argument_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an argument based on its meta-model ``identifier``.

    >>> argument_name(Identifier("something"))
    'something'

    >>> argument_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)


def variable_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a variable based on its meta-model ``identifier``.

    >>> variable_name(Identifier("something"))
    'something'

    >>> variable_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    return aas_core_codegen.naming.lower_camel_case(identifier)
