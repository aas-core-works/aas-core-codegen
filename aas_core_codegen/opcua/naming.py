"""Generate the names for the OPC UA nodeset definitions."""
import re

from aas_core_codegen.common import Identifier, Stripped
from aas_core_codegen import naming


def enum_name(identifier: Identifier, prefix: Identifier) -> Identifier:
    """
    Generate the name in OPC UA corresponding to the given enum identifier.

    >>> enum_name(Identifier("Something"), Identifier("AAS"))
    'AASSomethingDataType'

    >>> enum_name(Identifier("Something_better"), Identifier("AAS"))
    'AASSomethingBetterDataType'

    >>> enum_name(Identifier("Some_URL"), Identifier("AAS"))
    'AASSomeUrlDataType'
    """
    return Identifier(prefix + naming.capitalized_camel_case(identifier) + "DataType")


def constrained_primitive_name(
    identifier: Identifier, prefix: Identifier
) -> Identifier:
    """
    Generate the name in OPC UA for the given constrained primitive identifier.

    >>> constrained_primitive_name(Identifier("Something"), Identifier("AAS"))
    'AASSomethingDataType'

    >>> constrained_primitive_name(Identifier("Something_better"), Identifier("AAS"))
    'AASSomethingBetterDataType'

    >>> constrained_primitive_name(Identifier("Some_URL"), Identifier("AAS"))
    'AASSomeUrlDataType'
    """
    return Identifier(prefix + naming.capitalized_camel_case(identifier) + "DataType")


def class_name(identifier: Identifier, prefix: Identifier) -> Identifier:
    """
    Generate the name in OPC UA corresponding to the given class identifier.

    >>> class_name(Identifier("Something"), Identifier("AAS"))
    'AASSomethingType'

    >>> class_name(Identifier("Something_better"), Identifier("AAS"))
    'AASSomethingBetterType'

    >>> class_name(Identifier("Some_URL"), Identifier("AAS"))
    'AASSomeUrlType'
    """
    return Identifier(prefix + naming.capitalized_camel_case(identifier) + "Type")


def interface_name(identifier: Identifier, prefix: Identifier) -> Identifier:
    """
    Generate the interface name in OPC UA corresponding to the given identifier.

    >>> interface_name(Identifier("Something"), Identifier("AAS"))
    'IAASSomethingType'

    >>> interface_name(Identifier("Something_better"), Identifier("AAS"))
    'IAASSomethingBetterType'

    >>> interface_name(Identifier("Some_URL"), Identifier("AAS"))
    'IAASSomeUrlType'
    """
    return Identifier("I" + prefix + naming.capitalized_camel_case(identifier) + "Type")


def enum_literal_name(identifier: Identifier) -> Identifier:
    """
    Generate the name of an enumeration literal.

    >>> enum_literal_name(Identifier("Something"))
    'Something'

    >>> enum_literal_name(Identifier("Something_better"))
    'SomethingBetter'

    >>> enum_literal_name(Identifier("Some_URL"))
    'SomeUrl'
    """
    return naming.capitalized_camel_case(identifier)


def property_name(identifier: Identifier) -> Identifier:
    """
    Generate the corresponding name for the property.

    >>> property_name(Identifier("Something"))
    'something'

    >>> property_name(Identifier("Something_better"))
    'somethingBetter'

    >>> property_name(Identifier("Some_URL"))
    'someUrl'
    """
    return naming.lower_camel_case(identifier)


_NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]+")


def constraint_browser_name(invariant_identifier: Stripped) -> Identifier:
    """
    Transform the invariant identifier into a valid browser name.

    >>> constraint_browser_name(Stripped('AASd-128'))
    'ConstraintAasd128'

    >>> constraint_browser_name(Stripped('AASc-3a-050'))
    'ConstraintAasc3a050'

    >>> constraint_browser_name(Stripped('1'))
    'Constraint1'
    """
    parts = _NON_ALPHANUMERIC.split(invariant_identifier)

    parts_joined = "_".join(parts)

    return naming.capitalized_camel_case(Identifier(f"Constraint_{parts_joined}"))
