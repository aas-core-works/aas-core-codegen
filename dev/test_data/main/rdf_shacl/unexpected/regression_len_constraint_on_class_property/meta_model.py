"""
Regression
"""


@invariant(lambda self: len(self) >= 1, "Check if string is not empty.")
@invariant(
    lambda self: matches_XML_serializable_string(self),
    "Constraint AASd-130: An attribute with data type 'string' shall consist "
    "of these characters only: "
    r"^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]*$",
)
# fmt: on
class Non_empty_XML_serializable_string(str, DBC):
    r"""
    Represent a string with at least one character.

    The string should also be serializable to XML, which is the background for
    the following constraint.

    :constraint AASd-130:

        An attribute with data type "string" shall consist of these characters only:
        ^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\u00010000-\u0010FFFF]*$.
    """


@abstract
class Abstract_value(DBC):
    text: Non_empty_XML_serializable_string

    def __init__(self, text: Non_empty_XML_serializable_string) -> None:
        self.text = text


@invariant(
    lambda self: len(self.text) <= 18,
    "String shall have a maximum length of 1023 characters.",
)
class Value(Abstract_value):
    def __init__(self, text: Non_empty_XML_serializable_string) -> None:
        Abstract_value.__init__(self, text=text)


# fmt: off
@invariant(
    lambda self:
    not (self.value is not None)
    or len(self.value) >= 1,
    "Value must be either not set or have at least one item"
)
# fmt: on
class Something:
    value: Optional[Value]

    def __init__(self, value: Optional[Value]) -> None:
        self.value = value


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
