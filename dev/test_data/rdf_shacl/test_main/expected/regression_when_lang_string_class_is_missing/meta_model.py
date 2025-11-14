"""
We encountered a bug when designing V3.0. When the class ``Lang_string`` is missing,
RDF generation breaks as we hard-wired certain blocks to generate specific code
for that particular class.

This unit test tests that RDF+SHACL generation does not break even though the class
``Lang_string`` is missing.
"""


@abstract
class Something_abstract(DBC):
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


@invariant(
    lambda self: len(self.text) <= 128,
    "Text shall have a maximum length of 128 characters.",
)
class Something(Something_abstract, DBC):
    def __init__(self, text: str) -> None:
        Something_abstract.__init__(self, text=text)


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
