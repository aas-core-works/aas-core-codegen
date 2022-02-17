"""Generate names from our ``Pasal_case`` for the respective targets."""
from typing import List

from icontract import ensure

from aas_core_codegen.common import Identifier

UPPERCASE_ABBREVIATION_SET = {"IRI", "IRDI", "IEC", "URL"}


def json_property(identifier: Identifier) -> Identifier:
    """
    Generate a JSON name of a property based on its meta-model ``identifier``.

    >>> json_property(Identifier("something"))
    'something'

    >>> json_property(Identifier("something_to_URL"))
    'somethingToUrl'

    >>> json_property(Identifier("global_asset_ID"))
    'globalAssetId'

    >>> json_property(Identifier("specific_asset_IDs"))
    'specificAssetIds'
    """
    parts = identifier.split("_")

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    cased_parts = [parts[0].lower()]  # type: List[str]
    for part in parts[1:]:
        cased_parts.append(part.capitalize())

    return Identifier("".join(cased_parts))


# fmt: off
@ensure(
    lambda result: "_" not in result
) # This post-condition avoids naming conflicts with prefixing in the JSON schema.
# fmt: on
def json_model_type(identifier: Identifier) -> Identifier:
    """
    Generate the ``modelType`` of the class based on its meta-model ``identifier``.

    >>> json_model_type(Identifier("something"))
    'Something'

    >>> json_model_type(Identifier("Data_type_IEC_61360"))
    'DataTypeIEC61360'
    """
    parts = identifier.split("_")

    cased_parts = []  # type: List[str]
    for part in parts:
        if part.upper() in UPPERCASE_ABBREVIATION_SET:
            cased_parts.append(part.upper())
        else:
            cased_parts.append(part.capitalize())

    return Identifier("".join(cased_parts))


def xml_class_name(identifier: Identifier) -> Identifier:
    """
    Generate the XML tag name for the given class based on its ``identifier``.

    >>> xml_class_name(Identifier("something"))
    'something'

    >>> xml_class_name(Identifier("URL_to_something"))
    'urlToSomething'
    """
    parts = identifier.split("_")
    assert (
        len(parts) >= 1
    ), f"Expected at least one part for the valid identifier: {identifier}"

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    # pylint: disable=consider-using-f-string
    return Identifier(
        "{}{}".format(
            parts[0].lower(), "".join(part.capitalize() for part in parts[1:])
        )
    )


def xml_property(identifier: Identifier) -> Identifier:
    """
    Generate the XML name for the given property based on its ``identifier``.

    >>> xml_property(Identifier("something"))
    'something'

    >>> xml_property(Identifier("URL_to_something"))
    'urlToSomething'
    """
    parts = identifier.split("_")
    assert (
        len(parts) >= 1
    ), f"Expected at least one part for the valid identifier: {identifier}"

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    # pylint: disable=consider-using-f-string
    return Identifier(
        "{}{}".format(
            parts[0].lower(), "".join(part.capitalize() for part in parts[1:])
        )
    )
