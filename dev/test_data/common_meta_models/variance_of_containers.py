"""
Test the variance of the containers passed as arguments.

A read-only ``Sequence[...]`` argument of a verification function is generic if its
items are instances of a class with descendants, so that the sequences of
the descendants can be passed to it without a copy. The arguments of the methods
and the mutable ``List[...]`` arguments remain invariant.
"""

from typing import Final, List, Optional, Sequence, Set

from icontract import DBC, invariant


@abstract
@serialization(with_model_type=True)
class Item(DBC):
    name: str

    # NOTE (mristin):
    # The optional property mirrors ``Referable.ID_short`` in aas-core-meta V3.2,
    # see :func:`nicknames_are_unique`.
    nickname: Optional[str]

    def __init__(self, name: str, nickname: Optional[str] = None) -> None:
        self.name = name
        self.nickname = nickname


class Some_item(Item, DBC):
    def __init__(self, name: str, nickname: Optional[str] = None) -> None:
        Item.__init__(self, name, nickname)


class Special_item(Some_item, DBC):
    level: int

    def __init__(self, name: str, level: int, nickname: Optional[str] = None) -> None:
        Some_item.__init__(self, name, nickname)
        self.level = level


@verification
def names_are_unique(items: Sequence[Item]) -> bool:
    """
    Check that the names of the :paramref:`items` are unique.

    The :paramref:`items` are a generic sequence, so the sequences of
    the descendants of :class:`Item` can be passed without a copy.
    """
    name_set: Set[str] = set()
    for item in items:
        if item.name in name_set:
            return False

        name_set.add(item.name)

    return True


@verification
def names_are_non_empty(items: Sequence[Item]) -> bool:
    """Iterate over a generic sequence in a generator."""
    return all(len(item.name) > 0 for item in items)


@verification
def some_special_item_has_level(items: Sequence[Item]) -> bool:
    """Narrow the items of a generic sequence in a generator."""
    return any(isinstance(item, Special_item) and item.level > 0 for item in items)


@verification
def first_is_special(items: Sequence[Item]) -> bool:
    """Index a generic sequence, and narrow the item."""
    if len(items) == 0:
        return False

    first = items[0]
    if isinstance(first, Special_item):
        return first.level > 0

    return False


@verification
def nicknames_are_unique(items: Sequence[Item]) -> bool:
    """
    Check that the nicknames of the :paramref:`items` are unique, if specified.

    This mirrors the body of ``ID_shorts_are_unique`` in aas-core-meta V3.2:
    a local variable takes an optional property of an item of a generic sequence,
    and the loop continues if it is None.
    """
    nickname_set: Set[str] = set()
    for item in items:
        nickname = item.nickname
        if nickname is None:
            continue

        if nickname in nickname_set:
            return False

        nickname_set.add(nickname)

    return True


@verification
def levels_of_special_items_are_positive(items: Sequence[Item]) -> bool:
    """
    Narrow the loop variable over a generic sequence in a for-loop.

    The loop variable is of the type parameter in Go, so the down-cast needs to
    go through ``any(...)``, and of the template parameter in C++.
    """
    for item in items:
        if isinstance(item, Special_item):
            if item.level <= 0:
                return False

    return True


@verification
def last_is_special(items: Sequence[Item]) -> bool:
    """
    Narrow an immutable local variable which holds an item of a generic sequence.

    In contrast to :func:`first_is_special`, the local variable is annotated, so
    it is of the parent class instead of the type parameter. Hence, Go down-casts
    it without ``any(...)``, and C++ binds the item to a constant reference to
    the shared pointer of the parent class.
    """
    if len(items) == 0:
        return False

    last: Final[Item] = items[len(items) - 1]
    if isinstance(last, Special_item):
        return last.level > 0

    return False


@verification
def names_are_disjoint(
    items: Sequence[Item], other_items: Sequence[Some_item], shared_name: str
) -> bool:
    """
    Mix two generic sequences with an argument which is not generic.

    The names must differ, except for the :paramref:`shared_name`, which may repeat.

    Go declares two type parameters, and C++ two template parameters. The nested
    generators iterate over two different generic sequences, so their variables
    are of two different type parameters.
    """
    return all(
        all(
            item.name != other_item.name or item.name == shared_name
            for other_item in other_items
        )
        for item in items
    )


@verification
def aliased_names_are_unique(
    items: Sequence[Item], optional_items: Optional[Sequence[Item]]
) -> bool:
    """
    Use the immutable aliases of the generic sequences.

    An immutable alias of the very same type shares the type annotation of
    the aliased generic sequence, so it is a generic sequence itself. Go declares
    the alias with the type parameter, C++ with the template parameter, while C#
    and Java infer its type with ``var``. The ``alias_of_alias`` aliases an alias,
    and the ``optional_alias`` aliases an optional generic sequence.
    """
    alias: Final[Sequence[Item]] = items
    alias_of_alias: Final[Sequence[Item]] = alias
    optional_alias: Final[Optional[Sequence[Item]]] = optional_items

    for item in alias:
        if isinstance(item, Special_item):
            if item.level <= 0:
                return False

    return (
        all(len(item.name) > 0 for item in alias_of_alias)
        and names_are_unique(alias_of_alias)
        and optional_names_are_unique(optional_alias)
        and (optional_alias is None or names_are_unique(optional_alias))
    )


@verification
def contains_some_item(some_item: Some_item, items: Sequence[Item]) -> bool:
    """
    Look up an instance of a descendant in a generic sequence.

    Go compares the instances as ``any``'s, as the items are of the type parameter,
    and C++ converts the member to the shared pointer of :class:`Item` so that
    the raw pointers are comparable for any template parameter.
    """
    return some_item in items


@verification
def items_overlap(items: Sequence[Item], other_items: Sequence[Some_item]) -> bool:
    """
    Look up the items of a generic sequence in another generic sequence.

    The member and the items are of two different type parameters.
    """
    return any(other_item in items for other_item in other_items)


@verification
def contains_special_item(
    special_item: Special_item, items: Sequence[Special_item]
) -> bool:
    """
    Look up an instance in a sequence which is not generic.

    The :class:`Special_item` has no descendants, so the :paramref:`items` are not
    a generic sequence, but Go still compares the instances as ``any``'s.
    """
    return special_item in items


@verification
def container_names_are_unique(container: "Container") -> bool:
    """
    Pass the local variables on to generic sequences.

    The ``some_items`` is a read-only alias without an annotation, while
    the ``all_some_items`` is an immutable local variable declared with
    ``Final[...]``. Both hold the sequences of :class:`Some_item`, and are passed
    on to the generic sequences of :class:`Item`, required as well as optional.
    """
    some_items = container.some_items
    all_some_items: Final[Sequence[Some_item]] = container.some_items
    return (
        names_are_unique(some_items)
        and names_are_unique(all_some_items)
        and optional_names_are_unique(all_some_items)
    )


@verification
def optional_names_are_unique(items: Optional[Sequence[Item]]) -> bool:
    """Pass an optional generic sequence on to a generic sequence."""
    return items is None or names_are_unique(items)


@verification
def some_names_are_unique(
    some_items: Sequence[Some_item], special_items: Optional[Sequence[Special_item]]
) -> bool:
    """
    Pass the generic sequences of the descendants on.

    The :paramref:`some_items` are passed on as a required and as an optional
    sequence of the parent class, while the :paramref:`special_items` are passed on
    as an optional sequence and, once narrowed, as a required sequence of the parent
    class of the parent class.
    """
    return (
        names_are_unique(some_items)
        and optional_names_are_unique(some_items)
        and optional_names_are_unique(special_items)
        and optional_names_are_unique(None)
        and (special_items is None or names_are_unique(special_items))
    )


@verification
def levels_are_positive(items: Sequence[Special_item]) -> bool:
    """
    Check that the levels are positive.

    The :class:`Special_item` has no descendants, so the :paramref:`items` are not
    a generic sequence.
    """
    return all(item.level > 0 for item in items)


@invariant(
    lambda self: names_are_unique(self.items),
    "Names of the items must be unique.",
)
@invariant(
    lambda self: some_names_are_unique(self.some_items, self.special_items),
    "Names of some items and of special items must be unique.",
)
@invariant(
    lambda self: names_are_non_empty(self.some_items),
    "Names of some items must be non-empty.",
)
@invariant(
    lambda self: not some_special_item_has_level(self.items)
    or first_is_special(self.items),
    "If there is a special item with level, the first item must be special.",
)
@invariant(
    lambda self: not (self.special_items is not None)
    or levels_are_positive(self.special_items),
    "Levels of the special items must be positive.",
)
@invariant(
    lambda self: not (self.special_items is not None)
    or first_is_special(self.special_items),
    "The first special item must be special.",
)
@invariant(
    lambda self: optional_names_are_unique(self.special_items),
    "Names of the special items must be unique.",
)
@invariant(
    lambda self: self.count_items(self.items) == len(self.items),
    "Count of the items must match the number of the items.",
)
@invariant(
    lambda self: nicknames_are_unique(self.some_items),
    "Nicknames of some items must be unique.",
)
@invariant(
    lambda self: levels_of_special_items_are_positive(self.items),
    "Levels of the special items among the items must be positive.",
)
@invariant(
    lambda self: not some_special_item_has_level(self.items)
    or last_is_special(self.items),
    "If there is a special item with level, the last item must be special.",
)
@invariant(
    lambda self: names_are_disjoint(self.items, self.some_items, "x"),
    "Names of the items and of some items must be disjoint.",
)
@invariant(
    lambda self: aliased_names_are_unique(self.some_items, self.special_items),
    "Names of some items and of special items must be unique through aliases.",
)
@invariant(
    lambda self: all(
        contains_some_item(some_item, self.items) for some_item in self.some_items
    ),
    "Some items must be among the items.",
)
@invariant(
    lambda self: len(self.some_items) == 0
    or items_overlap(self.items, self.some_items),
    "If there are some items, they must overlap with the items.",
)
@invariant(
    lambda self: not (self.special_items is not None)
    or all(
        contains_special_item(special_item, self.special_items)
        for special_item in self.special_items
    ),
    "Each special item must be among the special items.",
)
class Container(DBC):
    items: List[Item]
    some_items: List[Some_item]
    special_items: Optional[List[Special_item]]

    @non_mutating
    def count_items(self, items: Sequence[Item]) -> int:
        """
        Count the :paramref:`items`.

        The arguments of the methods are never generic, so only the sequences of
        :class:`Item` can be passed to it, but not the sequences of
        the descendants.
        """
        return len(items)

    def __init__(
        self,
        items: List[Item],
        some_items: List[Some_item],
        special_items: Optional[List[Special_item]] = None,
    ) -> None:
        self.items = items
        self.some_items = some_items
        self.special_items = special_items


# NOTE (mristin):
# We pass the container as a property, since the C++ invariants hold ``self`` as
# a raw pointer, which can not be passed on to a verification function expecting
# a shared pointer.
@invariant(
    lambda self: container_names_are_unique(self.container),
    "Names of some items of the container must be unique.",
)
class Wrapper(DBC):
    container: Container

    def __init__(self, container: Container) -> None:
        self.container = container


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
