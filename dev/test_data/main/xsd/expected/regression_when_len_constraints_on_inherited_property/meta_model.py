"""
We encountered a bug when designing V3.0. The schema constraints on
the descendant classes where not inferred if an invariant  involved properties
inherited from the parent class.

This unit test illustrates the setting, and prevents regressions.
"""

# NOTE (mristin):
# The XSD generator expects the constrained primitive Value data type to be defined
# since we had to hard-wire it. If we remove that hard-wiring, we can also remove
# this definition as well.

class Value_data_type(str, DBC):
    pass



@abstract
@invariant(
    lambda self: len(self.text) >= 10,
    "String shall have a minimum length of 10 characters.",
)
@invariant(
    lambda self: len(self.text) <= 1024,
    "String shall have a maximum length of 1024 characters.",
)
class Abstract_lang_string(DBC):
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


# NOTE (mristin):
# The XSD is too complicated when it comes to tightening of constraints in children
# classes (there needs to be introduced two types: one for restricting the inherited
# properties and another one for extending them). At the moment (2026-04-29), we do not
# want to dive into that kind of complexity which would substantially change
# the resulting XSD schemas. Instead, we document the behavior in this test case.
@invariant(
    lambda self: len(self.text) <= 128,
    "String shall have a maximum length of 128 characters.",
)
class Lang_string_name_type(Abstract_lang_string, DBC):
    def __init__(self, text: str) -> None:
        Abstract_lang_string.__init__(self, text=text)


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
