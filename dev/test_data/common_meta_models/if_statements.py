from enum import Enum
from typing import List, Optional, Sequence

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


@abstract
@serialization(with_model_type=True)
class Parent(DBC):
    optional_text: Optional[str]

    def __init__(self, optional_text: Optional[str] = None) -> None:
        self.optional_text = optional_text


class Child_a(Parent):
    a_only: int

    def __init__(self, a_only: int, optional_text: Optional[str] = None) -> None:
        Parent.__init__(self, optional_text)
        self.a_only = a_only


class Child_b(Parent):
    b_only: int

    def __init__(self, b_only: int, optional_text: Optional[str] = None) -> None:
        Parent.__init__(self, optional_text)
        self.b_only = b_only


class Container(Parent):
    children: Optional[List[Parent]]

    def __init__(
        self,
        optional_text: Optional[str] = None,
        children: Optional[List[Parent]] = None,
    ) -> None:
        Parent.__init__(self, optional_text)
        self.children = children


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


@verification
def narrowing_in_body(parent: Optional[Parent]) -> bool:
    """Check the narrowing in the body of a branch by its condition."""
    if parent is not None and isinstance(parent, Child_a):
        return parent.a_only < 100

    return True


@verification
def narrowing_in_elif_and_else(parent: Optional[Parent]) -> bool:
    """Check the narrowing by the negation of the previous conditions."""
    if parent is None:
        return True
    elif not isinstance(parent, Child_b):
        return parent.optional_text is None or parent.optional_text != "forbidden"
    else:
        return parent.b_only > 0


@verification
def narrowing_after_early_return(parent: Optional[Parent]) -> bool:
    """Check the narrowing after an if-statement whose branch always returns."""
    if parent is None or not isinstance(parent, Child_b):
        return True

    return parent.b_only < 50


@verification
def narrowing_after_the_only_completing_branch(parent: Optional[Parent]) -> bool:
    """Check the narrowing after an if-statement whose ``else`` always returns."""
    if parent is not None and isinstance(parent, Child_a):
        pass
    else:
        return True

    return parent.a_only > -10


@verification
def child_as_have_texts(parents: Sequence[Parent]) -> bool:
    """Check the narrowing after the ``continue`` and the early return in a loop."""
    for parent in parents:
        if not isinstance(parent, Child_a):
            continue

        if parent.optional_text is None:
            return False

        if len(parent.optional_text) < 1:
            return False

    return True


@verification
def texts_before_container_are_short(parents: Sequence[Parent]) -> bool:
    """Check the narrowing after the ``continue`` in a loop with a ``break``."""
    total = 0
    for parent in parents:
        if isinstance(parent, Container):
            break

        if parent.optional_text is None:
            continue

        total = total + len(parent.optional_text)

    return total < 20


@verification
def text_or_default_is_short(parent: Parent) -> bool:
    """Check the narrowing by the value assigned in a branch."""
    text = parent.optional_text
    if text is None:
        text = "default"

    return len(text) < 10


@verification
def last_child_a_is_small(parent: Parent, parents: Sequence[Parent]) -> bool:
    """Check the narrowing of a variable to a class by the assigned value."""
    last = parent
    for other in parents:
        if isinstance(other, Child_a):
            last = other
            if last.a_only >= 1000:
                return False

    return True


@verification
def has_marker_in_tree(parent: Parent) -> bool:
    """Check the recursive chain of ``isinstance`` checks with early returns."""
    if parent.optional_text is not None and parent.optional_text == "marker":
        return True

    if isinstance(parent, Container):
        return parent.children is not None and any(
            has_marker_in_tree(child) for child in parent.children
        )

    return False


@invariant(
    lambda self: narrowing_in_body(self.optional_parent),
    "Optional parent as Child_a must have a small a_only",
)
@invariant(
    lambda self: narrowing_in_elif_and_else(self.optional_parent),
    "Optional parent must have an allowed text or a positive b_only",
)
@invariant(
    lambda self: narrowing_after_early_return(self.optional_parent),
    "Optional parent as Child_b must have a small b_only",
)
@invariant(
    lambda self: narrowing_after_the_only_completing_branch(self.optional_parent),
    "Optional parent as Child_a must have a_only above minus ten",
)
@invariant(
    lambda self: not (self.parents is not None) or child_as_have_texts(self.parents),
    "Parents as Child_a must have non-empty texts",
)
@invariant(
    lambda self: not (self.parents is not None)
    or texts_before_container_are_short(self.parents),
    "Texts of parents before the first container must be short",
)
@invariant(
    lambda self: not (self.optional_parent is not None)
    or text_or_default_is_short(self.optional_parent),
    "Text of the optional parent must be short",
)
@invariant(
    lambda self: not (self.optional_parent is not None and self.parents is not None)
    or last_child_a_is_small(self.optional_parent, self.parents),
    "Parents as Child_a must have a_only below one thousand",
)
@invariant(
    lambda self: not (self.optional_parent is not None)
    or not has_marker_in_tree(self.optional_parent),
    "Optional parent must have no marker in its tree",
)
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
    optional_parent: Optional[Parent]
    parents: Optional[List[Parent]]

    def __init__(
        self,
        kind: Kind,
        text: str,
        number: int,
        flag: bool,
        item: Item,
        optional_parent: Optional[Parent] = None,
        parents: Optional[List[Parent]] = None,
    ) -> None:
        self.kind = kind
        self.text = text
        self.number = number
        self.flag = flag
        self.item = item
        self.optional_parent = optional_parent
        self.parents = parents


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
