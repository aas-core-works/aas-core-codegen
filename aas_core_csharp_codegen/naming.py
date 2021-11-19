from typing import List

from aas_core_csharp_codegen.common import Identifier

UPPERCASE_ABBREVIATION_SET = {
    "IRI",
    "IRDI",
    "IEC",
    "ID",
    "URL"
}


def json_property(identifier: Identifier) -> Identifier:
    """
    Generate a JSON name of a property based on its meta-model ``identifier``.

    >>> json_property(Identifier("something"))
    'something'

    >>> json_property(Identifier("something_to_URL"))
    'somethingToURL'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    cased_parts = [parts[0].lower()]  # type: List[str]
    for part in parts[1:]:
        if part.upper() in UPPERCASE_ABBREVIATION_SET:
            cased_parts.append(part.upper())
        else:
            cased_parts.append(part.capitalize())

    return Identifier(''.join(cased_parts))


def json_model_type(identifier: Identifier) -> Identifier:
    """
    Generate the ``modelType`` of the class based on its meta-model ``identifier``.

    >>> json_model_type(Identifier("something"))
    'Something'

    >>> json_model_type(Identifier("Data_type_IEC_61360"))
    'DataTypeIEC61360'
    """
    parts = identifier.split('_')

    cased_parts = []  # type: List[str]
    for part in parts:
        if part.upper() in UPPERCASE_ABBREVIATION_SET:
            cased_parts.append(part.upper())
        else:
            cased_parts.append(part.capitalize())

    return Identifier(''.join(cased_parts))


def xml_name(identifier: Identifier) -> Identifier:
    """
    Generate the XML tag name for the given class based on its ``identifier``.

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
