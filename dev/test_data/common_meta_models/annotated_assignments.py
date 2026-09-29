"""
Check the transpilation of the variables declared with type annotations.

We also check ``None`` as a literal: assigned to the optional variables, passed as
an optional argument and returned from a method returning an optional.
"""
from enum import Enum
from typing import List, Optional, Sequence, Tuple, Union

from icontract import DBC, invariant


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"


@invariant(lambda self: len(self) > 0, "Code must not be empty.")
class Code(str):
    """Represent a non-empty code."""


class Item(DBC):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


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


Parent_or_item = Union[Parent, Item]

# NOTE (mristin):
# The roots of the union overlap, as ``Child_b`` is also a descendant of ``Parent``.
Wide_union = Union[Parent_or_item, Child_b]


@verification
def first_child_a_is_small(parents: Sequence[Parent]) -> bool:
    """Check an optional class declared with ``None`` and assigned in a loop."""
    found: Optional[Child_a] = None
    for parent in parents:
        if isinstance(parent, Child_a):
            found = parent
            break

    if found is None:
        return True

    return found.a_only < 100


@verification
def text_is_allowed_unless_long(text: Optional[str]) -> bool:
    """Check an optional reset to ``None`` in the branch where it is non-null."""
    trimmed: Optional[str] = text
    if trimmed is not None and len(trimmed) > 10:
        trimmed = None

    # NOTE (mristin):
    # The variable is not annotated, so it gets the type of the value,
    # ``Optional[str]``, and can be reset to ``None`` as well.
    fallback = text
    if fallback is not None and fallback == "none":
        fallback = None

    if trimmed is None or fallback is None:
        return True

    # NOTE (mristin):
    # Only the short texts are left after the reset.
    return trimmed != "forbidden" and len(trimmed) <= 10


@verification
def last_child_b_is_not_zero(parent: Parent, parents: Sequence[Parent]) -> bool:
    """Check a non-optional variable declared wider than its value."""
    last: Parent = parent
    for other in parents:
        last = other

    if isinstance(last, Child_b):
        return last.b_only != 0

    return True


@verification
def child_a_declarations_agree(parent: Parent) -> bool:
    """Check the declarations from a value narrowed by ``isinstance``."""
    if isinstance(parent, Child_a):
        child: Child_a = parent
        child_copy = parent

        # NOTE (mristin):
        # The variable is declared as ``Parent`` and stays so, as mypy does not
        # narrow the declared type by the initial value. However, the subsequent
        # assignment narrows it down to ``Child_a``.
        wider: Parent = parent
        if isinstance(wider, Child_b):
            return False

        wider = child

        return child.a_only == child_copy.a_only and wider.a_only > -1000

    return True


@verification
def optionals_from_values_are_small(number: int, optional_text: Optional[str]) -> bool:
    """Check the optionals declared with a non-optional and an optional value."""
    maybe_number: Optional[int] = number
    maybe_text: Optional[str] = optional_text

    # NOTE (mristin):
    # The declared ``maybe_number`` is optional, even though its value is not.
    if maybe_number is not None and maybe_number > 1000:
        return False

    if maybe_text is None:
        return True

    return len(maybe_text) < 20


@verification
def primitive_locals_are_consistent(text: str, number: int, flag: bool) -> bool:
    """Check the primitive declarations and their re-assignments."""
    count: int = 0
    if flag:
        count = count + 1

    size: int = len(text)
    ratio: float = 0.5
    enabled: bool = flag
    label: str = text

    if enabled and label == "bad" and count > 0:
        return False

    return ratio < 1.0 and size + number < 1000


@verification
def kinds_are_consistent(kind: Kind, optional_kind: Optional[Kind]) -> bool:
    """Check the declarations of the enumerations."""
    current: Kind = kind
    other: Optional[Kind] = None
    if optional_kind is not None:
        other = optional_kind

    if other is None:
        return True

    return current != Kind.Beta or other != Kind.Beta


@verification
def code_is_not_reserved(code: Code) -> bool:
    """Check the declarations of a constrained primitive."""
    exact: Code = code
    plain: str = code
    return exact != "reserved" and len(plain) < 10


@verification
def data_is_small(data: Optional[bytearray]) -> bool:
    """Check the declaration of an optional byte array."""
    trimmed: Optional[bytearray] = data
    if trimmed is None:
        return True

    return len(trimmed) < 10


@verification
def texts_are_few(
    texts: Sequence[str], optional_texts: Optional[Sequence[str]]
) -> bool:
    """Check the declarations of the lists."""
    all_texts: Sequence[str] = texts
    maybe_texts: Optional[List[str]] = optional_texts
    if maybe_texts is not None and len(maybe_texts) > 3:
        return False

    return len(all_texts) < 5


@verification
def tuples_are_consistent(
    text: str, number: int, optional_parent: Optional[Parent]
) -> bool:
    """Check the declarations of the tuples."""
    pair: Tuple[str, int] = (text, number)
    optional_pair: Optional[Tuple[str, Parent]] = None
    if optional_parent is not None:
        optional_pair = (text, optional_parent)

    if (
        optional_pair is not None
        and optional_pair[1].optional_text is not None
        and optional_pair[1].optional_text == "forbidden"
    ):
        return False

    return pair[1] < 1000


@verification
def union_locals_are_consistent(parent: Parent, item: Item) -> bool:
    """Check the declarations of the named unions."""
    # NOTE (mristin):
    # We wrap the root of the union.
    current: Parent_or_item = parent

    # NOTE (mristin):
    # We wrap a descendant of a root of the union, and the variable is narrowed
    # by the assigned value.
    if isinstance(parent, Child_a):
        current = parent
        if current.a_only == 13:
            return False

    current = item
    if len(current.name) < 1:
        return False

    optional_member: Optional[Parent_or_item] = None
    if isinstance(parent, Child_b):
        optional_member = parent

    if optional_member is not None and isinstance(optional_member, Child_b):
        if optional_member.b_only == 13:
            return False

    # NOTE (mristin):
    # We wrap into the most specific of the overlapping roots, ``Child_b``.
    wide: Wide_union = item
    if isinstance(parent, Child_b):
        wide = parent

    return not isinstance(wide, Child_b) or wide.b_only != 14


@verification
def member_is_lucky(member: Optional[Parent_or_item]) -> bool:
    """Check reading the optional named union of a property."""
    if member is not None and isinstance(member, Child_a):
        return member.a_only != 13

    return True


@verification
def wrap_into_member(something: Mutable["Something"], item: Mutable[Item]) -> bool:
    """Check wrapping an instance into the named union of a property."""
    something.optional_member = item
    return True


@verification
def text_is_short(text: Optional[str]) -> bool:
    """Check the optional text passed on as ``None`` from other functions."""
    return text is None or len(text) <= 10


@verification
def none_is_short_and_text_is_short(text: str) -> bool:
    """Check ``None`` passed as an optional argument."""
    return text_is_short(None) and text_is_short(text)


@invariant(
    lambda self: first_child_a_is_small(self.parents),
    "The first parent as Child_a must have a small a_only",
)
@invariant(
    lambda self: text_is_allowed_unless_long(self.optional_text),
    "Optional text must not be forbidden unless long",
)
@invariant(
    lambda self: last_child_b_is_not_zero(self.parent, self.parents),
    "The last parent as Child_b must have a non-zero b_only",
)
@invariant(
    lambda self: child_a_declarations_agree(self.parent),
    "Parent as Child_a must have a_only above minus one thousand",
)
@invariant(
    lambda self: optionals_from_values_are_small(self.number, self.optional_text),
    "Number must be at most one thousand and optional text short",
)
@invariant(
    lambda self: primitive_locals_are_consistent(self.text, self.number, self.flag),
    "Text must not be bad with the flag, and text and number must be small",
)
@invariant(
    lambda self: kinds_are_consistent(self.kind, self.optional_kind),
    "Kind and optional kind must not both be beta",
)
@invariant(
    lambda self: code_is_not_reserved(self.code),
    "Code must not be reserved and must be short",
)
@invariant(
    lambda self: data_is_small(self.optional_data),
    "Optional data must be small",
)
@invariant(
    lambda self: texts_are_few(self.texts, self.optional_texts),
    "Texts must be few",
)
@invariant(
    lambda self: tuples_are_consistent(self.text, self.number, self.optional_parent),
    "Optional parent must not have a forbidden text, and number must be small",
)
@invariant(
    lambda self: union_locals_are_consistent(self.parent, self.item),
    "Item must have a name, and parent must not have an unlucky number",
)
@invariant(
    lambda self: member_is_lucky(self.optional_member),
    "Optional member as Child_a must not have an unlucky a_only",
)
@invariant(
    lambda self: none_is_short_and_text_is_short(self.text),
    "Text must be at most 10 characters long",
)
@invariant(
    lambda self: self.text_or_alternative(None) != "forbidden",
    "Optional text or the default must not be forbidden",
)
@invariant(
    lambda self: self.number_or_alternative(None) != 666,
    "Number must not be 666",
)
@invariant(
    lambda self: self.text_is_not_bye(),
    "Text must not be bye",
)
@invariant(
    lambda self: self.first_child_b_is_not_forty_two(),
    "The first parent as Child_b must not have b_only of 42",
)
class Something(DBC):
    text: str
    number: int
    flag: bool
    kind: Kind
    code: Code
    item: Item
    parent: Parent
    parents: List[Parent]
    texts: List[str]
    optional_text: Optional[str]
    optional_kind: Optional[Kind]
    optional_parent: Optional[Parent]
    optional_texts: Optional[List[str]]
    optional_data: Optional[bytearray]
    optional_member: Optional[Parent_or_item]

    def set_member_to_item(self, item: Mutable[Item]) -> None:
        """Wrap :paramref:`item`, a root of the union, into the optional member."""
        self.optional_member = item

    def set_member_to_child_a(self, parent: Mutable[Parent]) -> None:
        """Wrap :paramref:`parent`, if a descendant of a root, or reset the member."""
        if isinstance(parent, Child_a):
            self.optional_member = parent
        else:
            self.optional_member = None

    @non_mutating
    def text_or_none(self, limit: int) -> Optional[str]:
        """Return the text if at most :paramref:`limit` long, and ``None`` otherwise."""
        if len(self.text) > limit:
            return None

        return self.text

    @non_mutating
    def text_or_alternative(self, alternative: Optional[str]) -> str:
        """Return the optional text, or :paramref:`alternative`, or a default."""
        result: Optional[str] = self.optional_text
        if result is None:
            result = alternative

        if result is None:
            return "default"

        return result

    @non_mutating
    def number_or_alternative(self, alternative: Optional[int]) -> int:
        """Return :paramref:`alternative`, if given, and the number otherwise."""
        result: Optional[int] = alternative
        if result is None:
            result = self.number

        return result

    @non_mutating
    def first_child_b_or_none(self) -> Optional[Child_b]:
        """Return the first parent which is a :class:`Child_b`, if any."""
        found: Optional[Child_b] = None
        for parent in self.parents:
            if isinstance(parent, Child_b):
                found = parent
                break

        return found

    @non_mutating
    def text_is_not_bye(self) -> bool:
        """Check a declaration from a method returning an optional."""
        short: Optional[str] = self.text_or_none(3)
        return short is None or short != "bye"

    @non_mutating
    def first_child_b_is_not_forty_two(self) -> bool:
        """Check a declaration of a class from a method returning an optional."""
        first: Optional[Child_b] = self.first_child_b_or_none()
        return first is None or first.b_only != 42

    def __init__(
        self,
        text: str,
        number: int,
        flag: bool,
        kind: Kind,
        code: Code,
        item: Item,
        parent: Parent,
        parents: List[Parent],
        texts: List[str],
        optional_text: Optional[str] = None,
        optional_kind: Optional[Kind] = None,
        optional_parent: Optional[Parent] = None,
        optional_texts: Optional[List[str]] = None,
        optional_data: Optional[bytearray] = None,
        optional_member: Optional[Parent_or_item] = None,
    ) -> None:
        self.text = text
        self.number = number
        self.flag = flag
        self.kind = kind
        self.code = code
        self.item = item
        self.parent = parent
        self.parents = parents
        self.texts = texts
        self.optional_text = optional_text
        self.optional_kind = optional_kind
        self.optional_parent = optional_parent
        self.optional_texts = optional_texts
        self.optional_data = optional_data
        self.optional_member = optional_member


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
