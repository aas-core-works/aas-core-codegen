"""
Generate C++ identifiers based on the identifiers from the meta-model.

The methods all generate public names, unless their prefix indicates
otherwise.

We follow the Google C++ code style,
see: https://google.github.io/styleguide/cppguide.html#Naming
"""

from aas_core_codegen import naming
from aas_core_codegen.common import Identifier


def interface_name(identifier: Identifier) -> Identifier:
    """Generate a C++ interface name based on its meta-model ``identifier``."""
    return Identifier(f"I{naming.capitalized_camel_case(identifier)}")


def enum_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for an enum based on its meta-model ``identifier``.

    >>> enum_name(Identifier("something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return naming.capitalized_camel_case(identifier)


def enum_literal_name(literal_name: Identifier) -> Identifier:
    """
    Generate a C++ name for an enum literal.

    >>> enum_literal_name(Identifier("ID_short"))
    'kIdShort'
    """
    return Identifier(f"k{naming.capitalized_camel_case(literal_name)}")


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for a class based on its meta-model ``identifier``.

    >>> class_name(Identifier("something"))
    'Something'

    >>> class_name(Identifier("URL_to_something"))
    'UrlToSomething'
    """
    return naming.capitalized_camel_case(identifier)


def getter_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for a property getter based on its meta-model ``identifier``.

    >>> getter_name(Identifier("something"))
    'something'

    >>> getter_name(Identifier("something_to_URL"))
    'something_to_url'
    """
    return naming.lower_pascal_case(identifier)


def mutable_getter_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for a property getter based on its meta-model ``identifier``.

    >>> mutable_getter_name(Identifier("something"))
    'mutable_something'

    >>> mutable_getter_name(Identifier("something_to_URL"))
    'mutable_something_to_url'
    """
    return naming.lower_pascal_case(Identifier(f"mutable_{identifier}"))


def setter_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for a property setter based on its meta-model ``identifier``.

    >>> setter_name(Identifier("something"))
    'set_something'

    >>> setter_name(Identifier("something_to_URL"))
    'set_something_to_url'
    """
    return naming.lower_pascal_case(Identifier(f"set_{identifier}"))


def private_property_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for a private property based on the ``identifier``.

    >>> private_property_name(Identifier("something"))
    'something_'

    >>> private_property_name(Identifier("something_to_URL"))
    'something_to_url_'
    """
    return Identifier(f"{naming.lower_pascal_case(identifier)}_")


def method_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for a member method based on its meta-model ``identifier``.

    >>> method_name(Identifier("do_something"))
    'DoSomething'

    >>> method_name(Identifier("do_something_to_URL"))
    'DoSomethingToUrl'
    """
    return naming.capitalized_camel_case(identifier)


def function_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a function from its meta-model ``identifier``.

    >>> function_name(Identifier("do_something"))
    'DoSomething'

    >>> function_name(Identifier("do_something_to_URL"))
    'DoSomethingToUrl'
    """
    return naming.capitalized_camel_case(identifier)


def argument_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for an argument based on its meta-model ``identifier``.

    >>> argument_name(Identifier("something"))
    'something'

    >>> argument_name(Identifier("something_to_URL"))
    'something_to_url'
    """
    return naming.lower_pascal_case(identifier)


def variable_name(identifier: Identifier) -> Identifier:
    """
    Generate a C++ name for a variable based on its meta-model ``identifier``.

    >>> variable_name(Identifier("something"))
    'something'

    >>> variable_name(Identifier("something_to_URL"))
    'something_to_url'
    """
    return naming.lower_pascal_case(identifier)


def constant_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a constant based on its meta-model ``identifier``.

    >>> constant_name(Identifier("something"))
    'kSomething'

    >>> constant_name(Identifier("URL_to_something"))
    'kUrlToSomething'
    """
    return Identifier(f"k{naming.capitalized_camel_case(identifier)}")
