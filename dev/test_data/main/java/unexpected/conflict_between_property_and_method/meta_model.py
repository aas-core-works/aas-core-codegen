"""
We transform the meta-model identifiers into Java identifiers using
camel casing, which merges every part of the identifier and capitalizes
each part after the first one. Capitalizing an all-uppercase part (such as
an acronym) lower-cases all but its first letter. This means that two
different meta-model identifiers, which differ only in the casing of
a part, result in one and the same Java identifier.

In this test, we explicitly test for such conflicts between a property and
a method, as both are members of the same Java class.
"""

class Something:
    something_to_url: str

    @implementation_specific
    def something_to_URL(self) -> str:
        return self.something_to_url

    def __init__(self, something_to_url: str) -> None:
        self.something_to_url = something_to_url

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
