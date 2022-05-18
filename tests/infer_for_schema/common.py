"""Provide functions shared among the tests."""
from typing import Tuple, MutableMapping

import tests.common
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.common import Identifier


def parse_to_symbol_table_and_something_cls(
    source: str,
) -> Tuple[intermediate.SymbolTable, intermediate.ClassUnion]:
    """
    Parse the ``source``.

    Return the symbol table and the symbol corresponding to the class ``Something``
    in the ``source``.
    """
    symbol_table, error = tests.common.translate_source_to_intermediate(source=source)
    assert error is None, tests.common.most_underlying_messages(error)
    assert symbol_table is not None
    something_cls = symbol_table.must_find(Identifier("Something"))
    assert isinstance(
        something_cls, (intermediate.AbstractClass, intermediate.ConcreteClass)
    )

    return symbol_table, something_cls


def parse_to_symbol_table_and_something_cls_and_constraints_by_class(
    source: str,
) -> Tuple[
    intermediate.SymbolTable,
    intermediate.ClassUnion,
    MutableMapping[intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty],
]:
    """
    Parse the ``source``.

    Return the symbol table and the symbol corresponding to the class ``Something``
    in the ``source`` as well as the the inferred constraints mapped by classes.
    """
    symbol_table, something_cls = parse_to_symbol_table_and_something_cls(source=source)

    constraints_by_class, error = infer_for_schema.infer_constraints_by_class(
        symbol_table=symbol_table
    )
    assert error is None, tests.common.most_underlying_messages(error)
    assert constraints_by_class is not None

    return symbol_table, something_cls, constraints_by_class
