from aas_core_csharp_codegen.common import Identifier


def json_name(identifier: Identifier) -> Identifier:
    """
    Generate a JSON name of a property based on its meta-model ``identifier``.

    >>> json_name(Identifier("something"))
    'something'

    >>> json_name(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    return Identifier(
        "{}{}".format(
            parts[0].lower(),
            ''.join(part.capitalize() for part in parts[1:])))
