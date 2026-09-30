"""
Check the transpilation of the ``assert`` statements.

The assertions hold for all the instances, valid or invalid, as the invariants
check their preconditions first. Hence, the generated SDKs never throw.
"""
from typing import List, Optional, Sequence

from icontract import DBC, invariant


@abstract
@serialization(with_model_type=True)
class Parent(DBC):
    number: int

    def __init__(self, number: int) -> None:
        self.number = number


class Child_a(Parent):
    a_only: int

    def __init__(self, number: int, a_only: int) -> None:
        Parent.__init__(self, number)
        self.a_only = a_only


class Child_b(Parent):
    def __init__(self, number: int) -> None:
        Parent.__init__(self, number)


@verification
def absolute_is_small(number: int) -> bool:
    """Check the assertion without a message."""
    absolute = number
    if number < 0:
        absolute = -number

    assert absolute >= 0

    return absolute < 1000


@verification
def optional_text_is_short(text: Optional[str]) -> bool:
    """Check the narrowing of an optional argument by an assertion."""
    assert text is not None, 'The caller must check the text for "None" — always'

    return len(text) < 10


@verification
def child_a_is_small(parent: Parent) -> bool:
    """Check the narrowing of an argument to a class by an assertion."""
    assert isinstance(parent, Child_a), "The caller must check for Child_a"

    return parent.a_only < 100


@verification
def few_matches(texts: Sequence[str], text: str) -> bool:
    """Check the assertion with an f-string as the message in a for-loop."""
    count = 0
    for other in texts:
        if other == text:
            count = count + 1

        assert count <= len(
            texts
        ), f"Expected at most {len(texts)} matches, but got {count}"

    return count < 3


@verification
def texts_are_consistent(texts: Sequence[str], text: str, number: int) -> bool:
    """Check the condition which the targets break over multiple lines."""
    if len(texts) >= 5 and len(text) == 0:
        return False

    assert (
        len(texts) < 5 or len(text) > 0 or number < -1000
    ), "The early return rules out many texts with an empty text"

    return True


@invariant(
    lambda self: absolute_is_small(self.number),
    "Number must be between minus one thousand and one thousand",
)
@invariant(
    lambda self: not (self.optional_text is not None)
    or optional_text_is_short(self.optional_text),
    "Optional text must be short",
)
@invariant(
    lambda self: not isinstance(self.parent, Child_a) or child_a_is_small(self.parent),
    "Parent as Child_a must have a small a_only",
)
@invariant(
    lambda self: few_matches(self.texts, self.text),
    "Text must appear at most twice in the texts",
)
@invariant(
    lambda self: texts_are_consistent(self.texts, self.text, self.number),
    "Many texts require a non-empty text",
)
@invariant(
    lambda self: self.doubled_number() != 666,
    "Doubled number must not be devilish",
)
class Something(DBC):
    number: int
    text: str
    texts: List[str]
    parent: Parent
    optional_text: Optional[str]

    @non_mutating
    def doubled_number(self) -> int:
        """Check the assertion in a method."""
        doubled = self.number + self.number
        assert doubled - self.number == self.number, "Doubling must be reversible"

        return doubled

    def __init__(
        self,
        number: int,
        text: str,
        texts: List[str],
        parent: Parent,
        optional_text: Optional[str] = None,
    ) -> None:
        self.number = number
        self.text = text
        self.texts = texts
        self.parent = parent
        self.optional_text = optional_text


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
