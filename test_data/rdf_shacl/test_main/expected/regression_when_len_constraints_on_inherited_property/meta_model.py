"""
We encountered a bug when designing V3.0. The length constraints on an inherited
property were not inferred properly.

We add the following test to make sure that the bug does not regress.
"""


@abstract
class Abstract_lang_string(DBC):
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


@invariant(
    lambda self: len(self.text) <= 128,
    "String shall have a maximum length of 128 characters.",
)
class Lang_string_name_type(Abstract_lang_string, DBC):
    def __init__(self, text: str) -> None:
        Abstract_lang_string.__init__(self, text=text)


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
