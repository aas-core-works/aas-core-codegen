"""
We transform the meta-model identifiers into TypeScript identifiers using
camel casing, which merges every part of the identifier and capitalizes
each part after the first one. Capitalizing an all-uppercase part (such as
an acronym) lower-cases all but its first letter. This means that two
different meta-model identifiers, which differ only in the casing of
a part, result in one and the same TypeScript identifier.

In this test, we explicitly test for such conflicts in the arguments
of the constructor.
"""

class Something:
    something_to_url: str
    something_to_URL: str

    def __init__(self, something_to_url: str, something_to_URL: str) -> None:
        self.something_to_url = something_to_url
        self.something_to_URL = something_to_URL

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
