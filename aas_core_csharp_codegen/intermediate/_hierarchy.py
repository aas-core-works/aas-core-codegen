"""Understand the hierarchy of entities in the symbol table as an ontology."""
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
    entities: Sequence[parse.Entity], parsed_symbol_table: parse.SymbolTable
) -> Optional[parse.Entity]:
    """
    Verify that ``entities`` are topologically sorted.

    :return: The first entity which is not fitting the expected order.
    """
    observed = set()  # type: Set[parse.Entity]
    for entity in entities:
        for parent_name in entity.inheritances:
            parent = parsed_symbol_table.must_find_entity(parent_name)
            if parent not in observed:
                return entity

        observed.add(entity)

    return None


class _UnverifiedOntology:
    """
    Provide an ontology computed from a symbol table.

    This private is explicitly made protected to signal that it has not been vetted
    yet and might be inconsistent. For example, there might be entities which have
    conflicting properties or methods with their antecedents.
    """

    #: Topologically sorted entities
    entities: Final[Sequence[parse.Entity]]

    #: Map entity 🠒 topologically sorted antecedents
    _antecedents_of: Final[Mapping[parse.Entity, Sequence[parse.AbstractEntity]]]

    # fmt: off
    @require(
        lambda entities, parsed_symbol_table:
        first_not_in_topological_order(entities, parsed_symbol_table) is None
    )
    @require(
        lambda entities: len(entities) == 0 or len(entities[0].inheritances) == 0,
        "Origins first",
    )
    @require(
        lambda entities: len(set(entities)) == len(entities),
        "Unique entities in the topological sort",
    )
    @ensure(
        lambda self, parsed_symbol_table: all(
            first_not_in_topological_order(
                entity_antecedents, parsed_symbol_table) is None
            for entity_antecedents in self._antecedents_of.values()
        )
    )
    # fmt: on
    def __init__(
        self, entities: Sequence[parse.Entity], parsed_symbol_table: parse.SymbolTable
    ) -> None:
        """Initialize with the given values and pre-compute the antecedents."""
        self.entities = entities

        antecedents_of = (
            dict()
        )  # type: MutableMapping[parse.Entity, List[parse.AbstractEntity]]

        order_of = {entity: i for i, entity in enumerate(entities)}

        for entity in entities:
            parents = [
                parsed_symbol_table.must_find_entity(parent_name)
                for parent_name in entity.inheritances
            ]

            parents_with_order = [(order_of[parent], parent) for parent in parents]

            sorted_parents = sorted(parents_with_order, key=lambda item: item[0])

            entity_antecedents = []  # type: List[parse.AbstractEntity]
            for _, parent in sorted_parents:
                assert parent in antecedents_of, (
                    f"Expected to process all the parent's of the entity {entity.name} "
                    f"before (due to topological sort), "
                    f"but the parent entity {parent.name} has not been processed"
                )

                entity_antecedents.extend(antecedents_of[parent])

                assert isinstance(parent, parse.AbstractEntity), (
                    f"Expected the parent of {entity.name} to be "
                    f"an abstract entity, but got: {parent}"
                )

                entity_antecedents.append(parent)

            antecedents_of[entity] = entity_antecedents

        self._antecedents_of = antecedents_of

    def list_antecedents(self, entity: parse.Entity) -> Sequence[parse.AbstractEntity]:
        """Retrieve the antecedents of the given entity."""
        result = self._antecedents_of.get(entity, None)
        if result is None:
            raise KeyError(
                "The antecedents for the entity {entity} have not been precomputed."
            )

        return result


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _topologically_sort(
    parsed_symbol_table: parse.SymbolTable,
) -> Tuple[Optional[_UnverifiedOntology], Optional[parse.Entity]]:
    """
    Sort topologically all the entities in the ``parsed_symbol_table``.

    :return: topologically sorted entities, or an entity in a cycle
    """
    # See https://en.wikipedia.org/wiki/Topological_sorting#Depth-first%20search
    # We use sorted containers to avoid non-deterministic behavior.

    result = []  # type: List[parse.Entity]

    without_permanent_marks = sortedcontainers.SortedSet(
        key=lambda an_entity: an_entity.name
    )  # type: sortedcontainers.SortedSet[parse.Entity]

    for symbol in parsed_symbol_table.symbols:
        if not isinstance(symbol, parse.Entity):
            continue

        without_permanent_marks.add(symbol)

    permanent_marks = sortedcontainers.SortedSet(
        key=lambda an_entity: an_entity.name
    )  # type: sortedcontainers.SortedSet[parse.Entity]

    temporary_marks = sortedcontainers.SortedSet(
        key=lambda an_entity: an_entity.name
    )  # type: sortedcontainers.SortedSet[parse.Entity]

    visited_more_than_once = None  # type: Optional[parse.Entity]

    def visit(entity: parse.Entity) -> None:
        nonlocal visited_more_than_once
        nonlocal result

        if visited_more_than_once:
            return

        if entity in permanent_marks:
            return

        if entity in temporary_marks:
            visited_more_than_once = entity
            return

        temporary_marks.add(entity)

        for an_identifier in entity.inheritances:
            a_symbol = parsed_symbol_table.must_find(an_identifier)
            assert isinstance(a_symbol, parse.AbstractEntity)

            visit(entity=a_symbol)

        temporary_marks.remove(entity)
        permanent_marks.add(entity)

        if entity in without_permanent_marks:
            without_permanent_marks.remove(entity)

        result.append(entity)

    while len(without_permanent_marks) > 0 and not visited_more_than_once:
        visit(without_permanent_marks[0])

    if visited_more_than_once:
        return None, visited_more_than_once

    return _UnverifiedOntology(
        entities=result, parsed_symbol_table=parsed_symbol_table), None


class Ontology(_UnverifiedOntology):
    """
    Provide an ontology computed from a symbol table.

    The ontology has been verified through :py:function`map_symbol_table_to_ontology`.
    """


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def map_symbol_table_to_ontology(
    parsed_symbol_table: parse.SymbolTable,
) -> Tuple[Optional[Ontology], Optional[List[Error]]]:
    """Infer the ontology of the entities from the ``parsed_symbol_table``."""
    ontology, visited_more_than_once = _topologically_sort(
        parsed_symbol_table=parsed_symbol_table)
    if visited_more_than_once is not None:
        return (
            None,
            [
                Error(
                    visited_more_than_once.node,
                    f"Expected no cycles in the inheritance, "
                    f"but the entity {visited_more_than_once.name} has been observed "
                    f"in a cycle",
                )
            ],
        )

    assert ontology is not None

    errors = []  # type: List[Error]

    # region Check that properties and methods do not conflict among antecedents

    for symbol in parsed_symbol_table.symbols:
        if not isinstance(symbol, parse.Entity):
            continue

        antecedents = ontology.list_antecedents(entity=symbol)

        observed_properties = dict()  # type: MutableMapping[str, parse.Entity]
        observed_methods = dict()  # type: MutableMapping[str, parse.Entity]

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
                        f"entity {observed_properties[prop.name].name}: {prop.name}",
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
                        f"entity {observed_methods[method.name].name}: {method.name}",
                    )
                )

    # endregion

    # region Check that antecedents do not have constructors if the entity lacks one

    for symbol in parsed_symbol_table.symbols:
        if not isinstance(symbol, parse.Entity):
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
                            f"The entity {symbol.name} does not specify "
                            f"a constructor, but the antecedent entity "
                            f"{antecedent.name} specifies a constructor with "
                            f"arguments: {argument_names_str}",
                        )
                    )

    # endregion

    if len(errors) > 0:
        return None, errors

    return cast(Ontology, ontology), None
