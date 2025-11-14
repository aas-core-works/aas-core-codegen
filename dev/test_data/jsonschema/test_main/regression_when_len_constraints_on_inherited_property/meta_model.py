"""
We encountered a bug when designing V3.0. The schema constraints on
the descendant classes where not inferred if an invariant  involved properties
inherited from the parent class.

This unit test illustrates the setting, and prevents regressions.
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


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
