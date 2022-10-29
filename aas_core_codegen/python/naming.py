"""Generate Python identifiers based on the identifiers from the meta-model."""
from typing import Union

from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier, assert_never


# NOTE (mristin, 2022-10-28):
# We introduce a separate uppercase abbreviation set for Python since
# changing the set in :py:mod:`aas_core_codegen.naming` would cause too many
# backward-incompatible changes in the generated schemas.

UPPERCASE_ABBREVIATION_SET = {"IRI", "IRDI", "IEC", "URL", "XSD", "XML", "JSON", "AAS"}


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


def enum_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an enum based on its meta-model ``identifier``.

    >>> enum_name(Identifier("something"))
    'Something'

    >>> enum_name(Identifier("URL_to_something"))
    'URLToSomething'
    """
    parts = identifier.split("_")

    return Identifier(
        "".join(
            part.capitalize() if part not in UPPERCASE_ABBREVIATION_SET else part
            for part in parts
        )
    )


def enum_literal_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an enum literal based on its meta-model ``identifier``.

    >>> enum_literal_name(Identifier("something"))
    'SOMETHING'

    >>> enum_literal_name(Identifier("URL_to_something"))
    'URL_TO_SOMETHING'
    """
    parts = identifier.split("_")

    return Identifier("_".join(part.upper() for part in parts))


def private_constant_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a constant based on its meta-model ``identifier``.

    >>> private_constant_name(Identifier("something"))
    '_SOMETHING'

    >>> private_constant_name(Identifier("URL_to_something"))
    '_URL_TO_SOMETHING'
    """
    parts = identifier.split("_")

    return Identifier("_" + "_".join(part.upper() for part in parts))


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


def private_class_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a priave class based on its meta-model ``identifier``.

    >>> private_class_name(Identifier("something"))
    '_Something'

    >>> private_class_name(Identifier("URL_to_something"))
    '_URLToSomething'
    """
    parts = identifier.split("_")

    return Identifier(
        "_"
        + "".join(
            part.capitalize() if part not in UPPERCASE_ABBREVIATION_SET else part
            for part in parts
        )
    )


def class_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a class based on its meta-model ``identifier``.

    >>> class_name(Identifier("something"))
    'Something'

    >>> class_name(Identifier("URL_to_something"))
    'URLToSomething'
    """
    parts = identifier.split("_")

    return Identifier(
        "".join(
            part.capitalize() if part not in UPPERCASE_ABBREVIATION_SET else part
            for part in parts
        )
    )


def property_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a public property based on its meta-model ``identifier``.

    >>> property_name(Identifier("something"))
    'something'

    >>> property_name(Identifier("something_to_URL"))
    'something_to_url'
    """
    parts = identifier.split("_")

    return Identifier("_".join(part.lower() for part in parts))


def private_property_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a private property based on the ``identifier``.

    >>> private_property_name(Identifier("something"))
    '_something'

    >>> private_property_name(Identifier("something_to_URL"))
    '_something_to_url'
    """
    parts = identifier.split("_")

    return Identifier("_{}".format("_".join(part.lower() for part in parts)))


def private_method_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a private method based on the ``identifier``.

    >>> private_method_name(Identifier("something"))
    '_something'

    >>> private_method_name(Identifier("something_to_URL"))
    '_something_to_url'
    """
    parts = identifier.split("_")

    return Identifier("_{}".format("_".join(part.lower() for part in parts)))


def private_function_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a private function from its meta-model ``identifier``.

    >>> private_function_name(Identifier("do_something"))
    '_do_something'

    >>> private_function_name(Identifier("do_something_to_URL"))
    '_do_something_to_url'
    """
    parts = identifier.split("_")

    return Identifier("_" + "_".join(part.lower() for part in parts))


def function_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a function from its meta-model ``identifier``.

    >>> function_name(Identifier("do_something"))
    'do_something'

    >>> function_name(Identifier("do_something_to_URL"))
    'do_something_to_url'
    """
    parts = identifier.split("_")

    return Identifier("_".join(part.lower() for part in parts))


def method_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an instance method based on its meta-model ``identifier``.

    >>> method_name(Identifier("do_something"))
    'do_something'

    >>> method_name(Identifier("do_something_to_URL"))
    'do_something_to_url'
    """
    parts = identifier.split("_")

    return Identifier("_".join(part.lower() for part in parts))


def argument_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for an argument based on its meta-model ``identifier``.

    >>> argument_name(Identifier("something"))
    'something'

    >>> argument_name(Identifier("something_to_URL"))
    'something_to_url'
    """
    parts = identifier.split("_")

    return Identifier("_".join(part.lower() for part in parts))


def variable_name(identifier: Identifier) -> Identifier:
    """
    Generate a name for a variable based on its meta-model ``identifier``.

    >>> variable_name(Identifier("something"))
    'something'

    >>> variable_name(Identifier("something_to_URL"))
    'something_to_url'
    """
    parts = identifier.split("_")

    return Identifier("_".join(part.lower() for part in parts))
