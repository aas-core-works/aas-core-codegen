from aas_core_csharp_codegen.common import Identifier


def json_property(identifier: Identifier) -> Identifier:
    """
    Generate a JSON name of a property based on its meta-model ``identifier``.

    >>> json_property(Identifier("something"))
    'something'

    >>> json_property(Identifier("something_to_URL"))
    'somethingToUrl'
    """
    parts = identifier.split('_')

    if len(parts) == 1:
        return Identifier(parts[0].lower())

    return Identifier(
        "{}{}".format(
            parts[0].lower(),
            ''.join(part.capitalize() for part in parts[1:])))

def json_model_type(identifier: Identifier) -> Identifier:
    """
        Generate the ``modelType`` of the class based on its meta-model ``identifier``.

        >>> json_model_type(Identifier("something"))
        'Something'

        >>> json_model_type(Identifier("URL_to_something"))
        'UrlToSomething'
        """
    parts = identifier.split('_')

    return Identifier("{}".format(''.join(part.capitalize() for part in parts)))