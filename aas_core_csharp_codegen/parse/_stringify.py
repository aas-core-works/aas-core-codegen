"""Stringify the parsed meta-model."""
from typing import Optional, Union

from aas_core_csharp_codegen import stringify
from aas_core_csharp_codegen.common import assert_never
from aas_core_csharp_codegen.parse._types import (
    AbstractEntity,
    Argument,
    AtomicTypeAnnotation,
    ConcreteEntity,
    Contract,
    Contracts,
    Default,
    Entity,
    Enumeration,
    EnumerationLiteral,
    Method,
    Property,
    SelfTypeAnnotation,
    Snapshot,
    SubscriptedTypeAnnotation,
    Symbol,
    SymbolTable,
    TypeAnnotation,
    UnverifiedSymbolTable, Description, Invariant,
)


def _stringify_atomic_type_annotation(
        type_annotation: AtomicTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=AtomicTypeAnnotation.__name__,
        properties=[stringify.Property("identifier", type_annotation.identifier)],
    )

    stringify.assert_compares_against_dict(result, type_annotation)
    return result


def _stringify_subscripted_type_annotation(
        type_annotation: SubscriptedTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=SubscriptedTypeAnnotation.__name__,
        properties=[
            stringify.Property("identifier", type_annotation.identifier),
            stringify.Property(
                "subscripts",
                [
                    _stringify_type_annotation(subscript)
                    for subscript in type_annotation.subscripts
                ],
            ),
        ],
    )

    stringify.assert_compares_against_dict(result, type_annotation)
    return result


def _stringify_type_annotation(type_annotation: TypeAnnotation) -> stringify.Entity:
    if isinstance(type_annotation, AtomicTypeAnnotation):
        return _stringify_atomic_type_annotation(type_annotation)

    elif isinstance(type_annotation, SubscriptedTypeAnnotation):
        return _stringify_subscripted_type_annotation(type_annotation)

    elif isinstance(type_annotation, SelfTypeAnnotation):
        result = stringify.Entity(name=SelfTypeAnnotation.__name__, properties=[])
        stringify.assert_compares_against_dict(result, type_annotation)
        return result

    else:
        assert_never(type_annotation)
        raise AssertionError(type_annotation)


def _stringify_description(description: Description) -> stringify.Entity:
    return stringify.Entity(
        name=Description.__name__,
        properties=[
            stringify.PropertyEllipsis("document", description.document),
            stringify.PropertyEllipsis("node", description.node)
        ])


def _stringify_property(prop: Property) -> stringify.Entity:
    result = stringify.Entity(
        name=Property.__name__,
        properties=[
            stringify.Property("name", prop.name),
            stringify.Property(
                "type_annotation", _stringify_type_annotation(prop.type_annotation)
            ),
            stringify.Property("description", _stringify_description(prop.description)),
            stringify.Property("is_readonly", prop.is_readonly),
            stringify.PropertyEllipsis("node", prop.node),
        ],
    )

    stringify.assert_compares_against_dict(result, prop)
    return result


def _stringify_default(default: Default) -> stringify.Entity:
    result = stringify.Entity(
        name=Default.__name__, properties=[
            stringify.PropertyEllipsis("node", default.node)]
    )

    stringify.assert_compares_against_dict(result, default)
    return result


def _stringify_argument(argument: Argument) -> stringify.Entity:
    result = stringify.Entity(
        name=Argument.__name__,
        properties=[
            stringify.Property("name", argument.name),
            stringify.Property(
                "type_annotation", _stringify_type_annotation(argument.type_annotation)
            ),
            stringify.Property(
                "default",
                None
                if argument.default is None
                else _stringify_default(argument.default),
            ),
            stringify.PropertyEllipsis("node", argument.node),
        ],
    )

    stringify.assert_compares_against_dict(result, argument)
    return result


def _stringify_invariant(invariant: Invariant) -> stringify.Entity:
    result = stringify.Entity(
        name=Invariant.__name__,
        properties=[
            stringify.Property(
                "description", _stringify_description(invariant.description)),
            stringify.PropertyEllipsis("condition", invariant.condition),
            stringify.PropertyEllipsis("node", invariant.node),
        ],
    )

    stringify.assert_compares_against_dict(result, invariant)
    return result


def _stringify_contract(contract: Contract) -> stringify.Entity:
    result = stringify.Entity(
        name=Contract.__name__,
        properties=[
            stringify.Property("args", contract.args),
            stringify.Property(
                "description", _stringify_description(contract.description)),
            stringify.PropertyEllipsis("condition", contract.condition),
            stringify.PropertyEllipsis("node", contract.node),
        ],
    )

    stringify.assert_compares_against_dict(result, contract)
    return result


def _stringify_snapshot(snapshot: Snapshot) -> stringify.Entity:
    result = stringify.Entity(
        name=Snapshot.__name__,
        properties=[
            stringify.Property("args", snapshot.args),
            stringify.Property("name", snapshot.name),
            stringify.PropertyEllipsis("capture", snapshot.capture),
            stringify.PropertyEllipsis("node", snapshot.node),
        ],
    )

    stringify.assert_compares_against_dict(result, snapshot)
    return result


def _stringify_contracts(contracts: Contracts) -> stringify.Entity:
    result = stringify.Entity(
        name=Contracts.__name__,
        properties=[
            stringify.Property(
                "preconditions",
                [_stringify_contract(contract) for contract in contracts.preconditions],
            ),
            stringify.Property(
                "snapshots",
                [_stringify_snapshot(snapshot) for snapshot in contracts.snapshots],
            ),
            stringify.Property(
                "postconditions",
                [
                    _stringify_contract(contract)
                    for contract in contracts.postconditions
                ],
            ),
        ],
    )

    stringify.assert_compares_against_dict(result, contracts)
    return result


def _stringify_method(method: Method) -> stringify.Entity:
    result = stringify.Entity(
        name=Method.__name__,
        properties=[
            stringify.Property("name", method.name),
            stringify.Property(
                "is_implementation_specific", method.is_implementation_specific
            ),
            stringify.Property(
                "arguments",
                [_stringify_argument(argument) for argument in method.arguments],
            ),
            stringify.PropertyEllipsis("argument_map", method.argument_map),
            stringify.Property(
                "returns",
                None
                if method.returns is None
                else _stringify_type_annotation(method.returns),
            ),
            stringify.Property(
                "description", _stringify_description(method.description)),
            stringify.Property("contracts", _stringify_contracts(method.contracts)),
            stringify.PropertyEllipsis("body", method.body),
            stringify.PropertyEllipsis("node", method.node),
        ],
    )

    stringify.assert_compares_against_dict(result, method)
    return result


def _stringify_symbol(symbol: Symbol) -> stringify.Entity:
    if isinstance(symbol, Entity):
        return _stringify_entity(symbol)

    elif isinstance(symbol, Enumeration):
        return _stringify_enumeration(symbol)

    else:
        assert_never(symbol)
        raise AssertionError(symbol)


def _stringify_entity(entity: Entity) -> stringify.Entity:
    result = stringify.Entity(
        name=entity.__class__.__name__,
        properties=[
            stringify.Property("name", entity.name),
            stringify.Property(
                "is_implementation_specific", entity.is_implementation_specific
            ),
            stringify.Property("inheritances", entity.inheritances),
            stringify.Property(
                "properties", [_stringify_property(prop) for prop in entity.properties]
            ),
            stringify.PropertyEllipsis("property_map", entity.property_map),
            stringify.Property(
                "methods", [_stringify_method(method) for method in entity.methods]
            ),
            stringify.PropertyEllipsis("method_map", entity.method_map),
            stringify.Property(
                "description", _stringify_description(entity.description)),
            stringify.PropertyEllipsis("node", entity.node),
        ],
    )

    stringify.assert_compares_against_dict(result, entity)
    return result


def _stringify_enumeration_literal(
        enumeration_literal: EnumerationLiteral,
) -> stringify.Entity:
    result = stringify.Entity(
        name=EnumerationLiteral.__name__,
        properties=[
            stringify.Property("name", enumeration_literal.name),
            stringify.Property("value", enumeration_literal.value),
            stringify.Property(
                "description", _stringify_description(enumeration_literal.description)),
            stringify.PropertyEllipsis("node", enumeration_literal.node),
        ],
    )

    stringify.assert_compares_against_dict(result, enumeration_literal)
    return result


def _stringify_enumeration(enumeration: Enumeration) -> stringify.Entity:
    result = stringify.Entity(
        name=Enumeration.__name__,
        properties=[
            stringify.Property("name", enumeration.name),
            stringify.Property(
                "literals",
                [
                    _stringify_enumeration_literal(literal)
                    for literal in enumeration.literals
                ],
            ),
            stringify.Property(
                "description", _stringify_description(enumeration.description)),
            stringify.PropertyEllipsis("node", enumeration.node),
        ],
    )

    stringify.assert_compares_against_dict(result, enumeration)
    return result


def _stringify_unverified_symbol_table(
        unverified_symbol_table: UnverifiedSymbolTable,
) -> stringify.Entity:
    entity = stringify.Entity(
        name=UnverifiedSymbolTable.__name__,
        properties=[
            stringify.Property(
                "symbols",
                [
                    _stringify_symbol(symbol)
                    for symbol in unverified_symbol_table.symbols
                ],
            )
        ],
    )

    stringify.assert_compares_against_dict(entity, unverified_symbol_table)
    return entity


def _stringify_symbol_table(symbol_table: SymbolTable) -> stringify.Entity:
    entity = stringify.Entity(
        name=SymbolTable.__name__,
        properties=[
            stringify.Property(
                "symbols",
                [_stringify_symbol(symbol) for symbol in symbol_table.symbols],
            )
        ],
    )

    stringify.assert_compares_against_dict(entity, symbol_table)
    return entity


Dumpable = Union[
    AbstractEntity,
    Argument,
    AtomicTypeAnnotation,
    ConcreteEntity,
    Contract,
    Contracts,
    Default,
    Entity,
    Enumeration,
    EnumerationLiteral,
    Invariant,
    Method,
    Property,
    SelfTypeAnnotation,
    Snapshot,
    SubscriptedTypeAnnotation,
    Symbol,
    SymbolTable,
    TypeAnnotation,
    UnverifiedSymbolTable,
]


def dump(dumpable: Dumpable) -> str:
    """Produce a string representation of the ``dumpable`` for testing or debugging."""
    stringified = None  # type: Optional[stringify.Entity]

    if isinstance(dumpable, Argument):
        stringified = _stringify_argument(dumpable)
    elif isinstance(dumpable, Contract):
        stringified = _stringify_contract(dumpable)
    elif isinstance(dumpable, Contracts):
        stringified = _stringify_contracts(dumpable)
    elif isinstance(dumpable, Default):
        stringified = _stringify_default(dumpable)
    elif isinstance(dumpable, Entity):
        stringified = _stringify_entity(dumpable)
    elif isinstance(dumpable, Enumeration):
        stringified = _stringify_enumeration(dumpable)
    elif isinstance(dumpable, EnumerationLiteral):
        stringified = _stringify_enumeration_literal(dumpable)
    elif isinstance(dumpable, Invariant):
        stringified = _stringify_invariant(dumpable)
    elif isinstance(dumpable, Method):
        stringified = _stringify_method(dumpable)
    elif isinstance(dumpable, Property):
        stringified = _stringify_property(dumpable)
    elif isinstance(dumpable, Snapshot):
        stringified = _stringify_snapshot(dumpable)
    elif isinstance(dumpable, (Enumeration, AbstractEntity, ConcreteEntity)):
        stringified = _stringify_symbol(dumpable)
    elif isinstance(dumpable, SymbolTable):
        stringified = _stringify_symbol_table(dumpable)
    elif isinstance(
            dumpable,
            (AtomicTypeAnnotation, SubscriptedTypeAnnotation, SelfTypeAnnotation)
    ):
        stringified = _stringify_type_annotation(dumpable)
    elif isinstance(dumpable, UnverifiedSymbolTable):
        stringified = _stringify_unverified_symbol_table(dumpable)
    else:
        assert_never(dumpable)

    assert stringified is not None

    assert isinstance(stringified, stringify.Entity)
    return stringify.dump(stringified)
