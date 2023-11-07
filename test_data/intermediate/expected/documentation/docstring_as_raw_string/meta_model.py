# We test for ``\x09`` and other special characters, and make sure they are represented
# adequately in the string dump of the symbol table.


class Non_empty_XML_serializable_string(str, DBC):
    r"""
    Represent a string with at least one character.

    The string should also be serializable to XML, which is the background for
    the following constraint.

    :constraint AASd-130:

        An attribute with data type "string" shall consist of these characters only:
        ``^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\u00010000-\u0010FFFF]*$``.
    """


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
