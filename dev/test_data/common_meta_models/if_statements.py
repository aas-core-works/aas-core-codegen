from enum import Enum
from typing import Optional

from icontract import DBC, invariant


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"
    Gamma = "gamma"


class Item(DBC):
    name: str
    optional_text: Optional[str]

    def __init__(self, name: str, optional_text: Optional[str] = None) -> None:
        self.name = name
        self.optional_text = optional_text


@verification
def if_with_a_single_branch(text: str) -> bool:
    """Check the if-statement with a single branch and no default."""
    if len(text) > 10:
        return False

    return True


@verification
def if_elif_else(number: int, text: str) -> bool:
    """
    Check the chain of ``if``, ``elif`` and ``else`` where all the branches return.

    The last ``elif`` compares against a constant, but it is still a branch of
    the if-statement as the chain does not start as a switch.
    """
    if number < 0 and len(text) > 0:
        return False
    elif number > 100 or text == "unlucky":
        return False
    elif number == 13:
        return False
    else:
        # NOTE (mristin):
        # We make the value long on purpose so that the targets break the line.
        doubled = number + number + number + number - number - number
        return doubled < 150


@verification
def if_with_pass(flag: bool, number: int) -> bool:
    """Check the if-statement with an empty branch."""
    if flag and number > 5:
        pass
    elif not flag:
        return number < 50

    return True


@verification
def if_in_default_of_switch(kind: Kind, number: int) -> bool:
    """
    Check the ``elif`` which does not compare the subject of the switch.

    The ``elif`` becomes an if-statement in the default of the switch, and nests
    a switch in turn.
    """
    if kind == Kind.Alpha:
        return number < 10
    elif number < -5:
        if kind == Kind.Beta:
            return False

    return True


@verification
def if_with_non_null_in_condition(item: Item) -> bool:
    """Check the condition which guards an optional value itself."""
    if item.optional_text is not None and len(item.optional_text) > 5:
        return False

    return True


@verification
def if_with_reassigned_variable(number: int) -> bool:
    """Check the variable defined before the if-statement and assigned in it."""
    result = 0
    if number > 20 and number < 30:
        result = number
    elif number < -20:
        result = -number

    return result < 25


@verification
def if_with_continue_in_for(number: int) -> bool:
    """Check the ``continue`` in a branch of an if-statement nested in a for-loop."""
    count = 0
    for i in range(0, 10):
        if i % 2 == 0 or i > number:
            continue

        count = count + 1

    return count != 3


@invariant(
    lambda self: if_with_a_single_branch(self.text),
    "Text must be at most 10 characters long",
)
@invariant(
    lambda self: if_elif_else(self.number, self.text),
    "Number and text must be acceptable",
)
@invariant(
    lambda self: if_with_pass(self.flag, self.number),
    "Number must be small without the flag",
)
@invariant(
    lambda self: if_in_default_of_switch(self.kind, self.number),
    "Number must be consistent with the kind",
)
@invariant(
    lambda self: if_with_non_null_in_condition(self.item),
    "Optional text of the item must be at most 5 characters long",
)
@invariant(
    lambda self: if_with_reassigned_variable(self.number),
    "Number must be neither between 25 and 29 nor below -24",
)
@invariant(
    lambda self: if_with_continue_in_for(self.number),
    "Number must not be five or six",
)
class Something(DBC):
    kind: Kind
    text: str
    number: int
    flag: bool
    item: Item

    def __init__(
        self, kind: Kind, text: str, number: int, flag: bool, item: Item
    ) -> None:
        self.kind = kind
        self.text = text
        self.number = number
        self.flag = flag
        self.item = item


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
