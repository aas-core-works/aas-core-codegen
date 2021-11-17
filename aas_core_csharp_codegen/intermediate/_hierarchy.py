"""Understand the hierarchy of classes in the symbol table as an ontology."""
from typing import (
    Sequence,
    Optional,
    Set,
    Final,
    Mapping,
    MutableMapping,
    List,
    cast,
    Tuple,
)

import sortedcontainers
from icontract import require, ensure

from aas_core_csharp_codegen import parse
from aas_core_csharp_codegen.common import Error, Identifier


def first_not_in_topological_order(
    classes: Sequence[parse.Class], parsed_symbol_table: parse.SymbolTable
) -> Optional[parse.Class]:
    """
    Verify that ``classes`` are topologically sorted.

    :return: The first class which is not fitting the expected order.
    """
    observed = set()  # type: Set[parse.Class]
    for cls in classes:
        for parent_name in cls.inheritances:
            parent = parsed_symbol_table.must_find_class(parent_name)
            if parent not in observed:
                return cls

        observed.add(cls)

    return None


class _UnverifiedOntology:
    """
    Provide an ontology computed from a symbol table.

    This private is explicitly made protected to signal that it has not been vetted
    yet and might be inconsistent. For example, there might be classes which have
    conflicting properties or methods with their antecedents.
    """

    #: Topologically sorted classes
    classes: Final[Sequence[parse.Class]]

    #: Map class 🠒 topologically sorted antecedents
    _antecedents_of: Final[Mapping[parse.Class, Sequence[parse.AbstractClass]]]

    # fmt: off
    @require(
        lambda classes, parsed_symbol_table:
        first_not_in_topological_order(classes, parsed_symbol_table) is None
    )
    @require(
        lambda classes: len(classes) == 0 or len(classes[0].inheritances) == 0,
        "Origins first",
    )
    @require(
        lambda classes: len(set(classes)) == len(classes),
        "Unique classes in the topological sort",
    )
    @ensure(
        lambda self, parsed_symbol_table: all(
            first_not_in_topological_order(
                class_antecedents, parsed_symbol_table) is None
            for class_antecedents in self._antecedents_of.values()
        )
    )
    # fmt: on
    def __init__(
        self, classes: Sequence[parse.Class], parsed_symbol_table: parse.SymbolTable
    ) -> None:
        """Initialize with the given values and pre-compute the antecedents."""
        self.classes = classes

        antecedents_of = (
            dict()
        )  # type: MutableMapping[parse.Class, List[parse.AbstractClass]]

        order_of = {cls: i for i, cls in enumerate(classes)}

        for cls in classes:
            parents = [
                parsed_symbol_table.must_find_class(parent_name)
                for parent_name in cls.inheritances
            ]

            parents_with_order = [(order_of[parent], parent) for parent in parents]

            sorted_parents = sorted(parents_with_order, key=lambda item: item[0])

            class_antecedents = []  # type: List[parse.AbstractClass]
            for _, parent in sorted_parents:
                assert parent in antecedents_of, (
                    f"Expected to process all the parent's of the class {cls.name} "
                    f"before (due to topological sort), "
                    f"but the parent class {parent.name} has not been processed"
                )

                class_antecedents.extend(antecedents_of[parent])

                assert isinstance(parent, parse.AbstractClass), (
                    f"Expected the parent of {cls.name} to be "
                    f"an abstract class, but got: {parent}"
                )

                class_antecedents.append(parent)

            antecedents_of[cls] = class_antecedents

        self._antecedents_of = antecedents_of

    def list_antecedents(self, cls: parse.Class) -> Sequence[parse.AbstractClass]:
        """Retrieve the antecedents of the given class ``cls``."""
        result = self._antecedents_of.get(cls, None)
        if result is None:
            raise KeyError(
                f"The antecedents for the class {cls} have not been precomputed."
            )

        return result


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _topologically_sort(
    parsed_symbol_table: parse.SymbolTable,
) -> Tuple[Optional[_UnverifiedOntology], Optional[parse.Class]]:
    """
    Sort topologically all the classes in the ``parsed_symbol_table``.

    :return: topologically sorted classes, or a class in a cycle
    """
    # See https://en.wikipedia.org/wiki/Topological_sorting#Depth-first%20search
    # We use sorted containers to avoid non-deterministic behavior.

    result = []  # type: List[parse.Class]

    without_permanent_marks = sortedcontainers.SortedSet(
        key=lambda a_class: a_class.name
    )  # type: sortedcontainers.SortedSet[parse.Class]

    for symbol in parsed_symbol_table.symbols:
        if not isinstance(symbol, parse.Class):
            continue

        without_permanent_marks.add(symbol)

    permanent_marks = sortedcontainers.SortedSet(
        key=lambda a_class: a_class.name
    )  # type: sortedcontainers.SortedSet[parse.Class]

    temporary_marks = sortedcontainers.SortedSet(
        key=lambda a_class: a_class.name
    )  # type: sortedcontainers.SortedSet[parse.Class]

    visited_more_than_once = None  # type: Optional[parse.Class]

    def visit(cls: parse.Class) -> None:
        nonlocal visited_more_than_once
        nonlocal result

        if visited_more_than_once:
            return

        if cls in permanent_marks:
            return

        if cls in temporary_marks:
            visited_more_than_once = cls
            return

        temporary_marks.add(cls)

        for an_identifier in cls.inheritances:
            a_symbol = parsed_symbol_table.must_find(an_identifier)
            assert isinstance(a_symbol, parse.AbstractClass)

            visit(cls=a_symbol)

        temporary_marks.remove(cls)
        permanent_marks.add(cls)

        if cls in without_permanent_marks:
            without_permanent_marks.remove(cls)

        result.append(cls)

    while len(without_permanent_marks) > 0 and not visited_more_than_once:
        visit(without_permanent_marks[0])

    if visited_more_than_once:
        return None, visited_more_than_once

    return _UnverifiedOntology(
        classes=result, parsed_symbol_table=parsed_symbol_table), None


class Ontology(_UnverifiedOntology):
    """
    Provide an ontology computed from a symbol table.

    The ontology has been verified through :py:function`map_symbol_table_to_ontology`.
    """


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def map_symbol_table_to_ontology(
    parsed_symbol_table: parse.SymbolTable,
) -> Tuple[Optional[Ontology], Optional[List[Error]]]:
    """Infer the ontology of the classes from the ``parsed_symbol_table``."""
    ontology, visited_more_than_once = _topologically_sort(
        parsed_symbol_table=parsed_symbol_table)
    if visited_more_than_once is not None:
        return (
            None,
            [
                Error(
                    visited_more_than_once.node,
                    f"Expected no cycles in the inheritance, "
                    f"but the class {visited_more_than_once.name} has been observed "
                    f"in a cycle",
                )
            ],
        )

    assert ontology is not None

    errors = []  # type: List[Error]

    # region Check that properties and methods do not conflict among antecedents

    for symbol in parsed_symbol_table.symbols:
        if not isinstance(symbol, parse.Class):
            continue

        antecedents = ontology.list_antecedents(cls=symbol)

        observed_properties = dict()  # type: MutableMapping[str, parse.Class]
        observed_methods = dict()  # type: MutableMapping[str, parse.Class]

        for antecedent in antecedents:
            for prop in antecedent.properties:
                if prop.name not in observed_properties:
                    observed_properties[prop.name] = antecedent

            for method in antecedent.methods:
                if method.name not in observed_properties:
                    observed_methods[method.name] = antecedent

        for prop in symbol.properties:
            if prop.name in observed_properties:
                errors.append(
                    Error(
                        prop.node,
                        f"The property has already been defined in the antecedent "
                        f"class {observed_properties[prop.name].name}: {prop.name}",
                    )
                )

        for method in symbol.methods:
            if method.name == "__init__":
                continue

            if method.name in observed_methods:
                errors.append(
                    Error(
                        method.node,
                        f"The method has already been defined in the antecedent "
                        f"class {observed_methods[method.name].name}: {method.name}",
                    )
                )

    # endregion

    # region Check that antecedents do not have constructors if the class lacks one

    for symbol in parsed_symbol_table.symbols:
        if not isinstance(symbol, parse.Class):
            continue

        if "__init__" not in symbol.method_map:
            for antecedent in ontology.list_antecedents(symbol):
                antecedent_init = antecedent.method_map.get(
                    Identifier("__init__"), None
                )

                if antecedent_init is not None and len(antecedent_init.arguments) > 1:
                    argument_names_str = ", ".join(
                        arg.name for arg in antecedent_init.arguments
                    )

                    errors.append(
                        Error(
                            symbol.node,
                            f"The class {symbol.name} does not specify "
                            f"a constructor, but the antecedent class "
                            f"{antecedent.name} specifies a constructor with "
                            f"arguments: {argument_names_str}",
                        )
                    )

    # endregion

    if len(errors) > 0:
        return None, errors

    return cast(Ontology, ontology), None
