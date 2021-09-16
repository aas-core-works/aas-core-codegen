"""Stringify the intermediate representation."""
from typing import Union, Optional

from aas_core_csharp_codegen import stringify
from aas_core_csharp_codegen.common import assert_never
from aas_core_csharp_codegen.intermediate._types import (
    Argument,
    AtomicTypeAnnotation,
    Class,
    Constructor,
    Contract,
    Contracts,
    Default,
    Enumeration,
    EnumerationLiteral,
    Interface,
    Method,
    Property,
    SelfTypeAnnotation,
    Signature,
    Snapshot,
    SubscriptedTypeAnnotation,
    Symbol,
    SymbolTable,
    TypeAnnotation, ListTypeAnnotation, SequenceTypeAnnotation, SetTypeAnnotation,
    MappingTypeAnnotation, MutableMappingTypeAnnotation, OptionalTypeAnnotation,
    BuiltinAtomicTypeAnnotation, OurAtomicTypeAnnotation, Description
)


def _stringify_default(default: Default) -> stringify.Entity:
    result = stringify.Entity(
        name=Default.__name__,
        properties=[
            stringify.Property("value", default.value),
            stringify.PropertyEllipsis("parsed", default.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, default)
    return result


def _stringify_atomic_type_annotation(
        type_annotation: AtomicTypeAnnotation,
) -> stringify.Entity:
    result = None  # type: Optional[stringify.Entity]

    if isinstance(type_annotation, BuiltinAtomicTypeAnnotation):
        result = stringify.Entity(
            name=AtomicTypeAnnotation.__name__,
            properties=[
                stringify.Property("a_type", type_annotation.a_type.value),
                stringify.PropertyEllipsis("parsed", type_annotation.parsed),
            ])
    elif isinstance(type_annotation, OurAtomicTypeAnnotation):
        result = stringify.Entity(
            name=AtomicTypeAnnotation.__name__,
            properties=[
                stringify.Property("symbol", type_annotation.symbol.name),
                stringify.PropertyEllipsis("parsed", type_annotation.parsed),
            ])
    else:
        assert_never(type_annotation)

    assert result is not None
    stringify.assert_compares_against_dict(result, type_annotation)
    return result


def _stringify_subscripted_type_annotation(
        type_annotation: SubscriptedTypeAnnotation,
) -> stringify.Entity:
    result = None  # type: Optional[stringify.Entity]

    if isinstance(type_annotation, ListTypeAnnotation):
        result = stringify.Entity(
            name=ListTypeAnnotation.__name__,
            properties=[
                stringify.Property(
                    "items", _stringify_type_annotation(type_annotation.items)),
                stringify.PropertyEllipsis("parsed", type_annotation.parsed),
            ])
    elif isinstance(type_annotation, SequenceTypeAnnotation):
        result = stringify.Entity(
            name=SequenceTypeAnnotation.__name__,
            properties=[
                stringify.Property(
                    "items", _stringify_type_annotation(type_annotation.items)),
                stringify.PropertyEllipsis("parsed", type_annotation.parsed),
            ])
    elif isinstance(type_annotation, SetTypeAnnotation):
        result = stringify.Entity(
            name=SetTypeAnnotation.__name__,
            properties=[
                stringify.Property(
                    "items", _stringify_type_annotation(type_annotation.items)),
                stringify.PropertyEllipsis("parsed", type_annotation.parsed),
            ])
    elif isinstance(type_annotation, MappingTypeAnnotation):
        result = stringify.Entity(
            name=MappingTypeAnnotation.__name__,
            properties=[
                stringify.Property(
                    "keys", _stringify_type_annotation(type_annotation.keys)),
                stringify.Property(
                    "values", _stringify_type_annotation(type_annotation.values)),
                stringify.PropertyEllipsis("parsed", type_annotation.parsed),
            ])
    elif isinstance(type_annotation, MutableMappingTypeAnnotation):
        result = stringify.Entity(
            name=MutableMappingTypeAnnotation.__name__,
            properties=[
                stringify.Property(
                    "keys", _stringify_type_annotation(type_annotation.keys)),
                stringify.Property(
                    "values", _stringify_type_annotation(type_annotation.values)),
                stringify.PropertyEllipsis("parsed", type_annotation.parsed),
            ])
    elif isinstance(type_annotation, OptionalTypeAnnotation):
        result = stringify.Entity(
            name=OptionalTypeAnnotation.__name__,
            properties=[
                stringify.Property(
                    "value", _stringify_type_annotation(type_annotation.value)),
                stringify.PropertyEllipsis("parsed", type_annotation.parsed),
            ])
    else:
        assert_never(type_annotation)

    assert result is not None
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
            stringify.PropertyEllipsis("parsed", argument.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, argument)
    return result


def _stringify_description(description: Description) -> stringify.Entity:
    return stringify.Entity(
        name=Description.__name__,
        properties=[
            stringify.PropertyEllipsis("document", description.document),
            stringify.PropertyEllipsis("node", description.node)
        ])


def _stringify_signature(signature: Signature) -> stringify.Entity:
    result = stringify.Entity(
        name=Signature.__name__,
        properties=[
            stringify.Property("name", signature.name),
            stringify.Property(
                "arguments",
                [_stringify_argument(argument) for argument in signature.arguments],
            ),
            stringify.Property(
                "returns",
                None
                if signature.returns is None
                else _stringify_type_annotation(signature.returns),
            ),
            stringify.Property(
                "description", _stringify_description(signature.description)),
            stringify.PropertyEllipsis("parsed", signature.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, signature)
    return result


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
            stringify.PropertyEllipsis("parsed", prop.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, prop)
    return result


def _stringify_interface(interface: Interface) -> stringify.Entity:
    result = stringify.Entity(
        name=Interface.__name__,
        properties=[
            stringify.Property("name", interface.name),
            stringify.Property("inheritances", interface.inheritances),
            stringify.Property(
                "signatures",
                [_stringify_signature(signature) for signature in interface.signatures],
            ),
            stringify.Property(
                "properties",
                [_stringify_property(prop) for prop in interface.properties],
            ),
            stringify.Property(
                "is_implementation_specific", interface.is_implementation_specific
            ),
            stringify.PropertyEllipsis("parsed", interface.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, interface)
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
            stringify.PropertyEllipsis("parsed", enumeration_literal.parsed),
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
            stringify.PropertyEllipsis("parsed", enumeration.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, enumeration)
    return result


def _stringify_contract(contract: Contract) -> stringify.Entity:
    result = stringify.Entity(
        name=Contract.__name__,
        properties=[
            stringify.Property("args", contract.args),
            stringify.Property(
                "description", _stringify_description(contract.description)),
            stringify.PropertyEllipsis("body", contract.body),
            stringify.PropertyEllipsis("parsed", contract.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, contract)
    return result


def _stringify_snapshot(snapshot: Snapshot) -> stringify.Entity:
    result = stringify.Entity(
        name=Snapshot.__name__,
        properties=[
            stringify.Property("args", snapshot.args),
            stringify.PropertyEllipsis("body", snapshot.body),
            stringify.Property("name", snapshot.name),
            stringify.PropertyEllipsis("parsed", snapshot.parsed),
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
            stringify.PropertyEllipsis("parsed", method.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, method)
    return result


def _stringify_constructor(constructor: Constructor) -> stringify.Entity:
    result = stringify.Entity(
        name=Constructor.__name__,
        properties=[
            stringify.Property(
                "arguments",
                [_stringify_argument(argument) for argument in constructor.arguments],
            ),
            stringify.Property(
                "contracts", _stringify_contracts(constructor.contracts)
            ),
            stringify.Property(
                "is_implementation_specific", constructor.is_implementation_specific
            ),
            stringify.PropertyEllipsis("statements", constructor.statements),
        ],
    )

    stringify.assert_compares_against_dict(result, constructor)
    return result


def _stringify_class(cls: Class) -> stringify.Entity:
    result = stringify.Entity(
        name=Class.__name__,
        properties=[
            stringify.Property("name", cls.name),
            stringify.Property("interfaces", cls.interfaces),
            stringify.Property(
                "is_implementation_specific", cls.is_implementation_specific
            ),
            stringify.Property(
                "properties", [_stringify_property(prop) for prop in cls.properties]
            ),
            stringify.Property(
                "methods", [_stringify_method(method) for method in cls.methods]
            ),
            stringify.Property("constructor", _stringify_constructor(cls.constructor)),
            stringify.Property("description", _stringify_description(cls.description)),
            stringify.PropertyEllipsis("parsed", cls.parsed),
        ],
    )

    stringify.assert_compares_against_dict(result, cls)
    return result


def _stringify_symbol(symbol: Symbol) -> stringify.Entity:
    if isinstance(symbol, Interface):
        return _stringify_interface(symbol)
    elif isinstance(symbol, Enumeration):
        return _stringify_enumeration(symbol)
    elif isinstance(symbol, Class):
        return _stringify_class(symbol)
    else:
        assert_never(symbol)
        raise AssertionError(symbol)


def _stringify_symbol_table(symbol_table: SymbolTable) -> stringify.Entity:
    """Represent the symbol table as a string for testing or debugging."""
    result = stringify.Entity(
        name=SymbolTable.__name__,
        properties=[
            stringify.Property(
                name="symbols",
                value=[_stringify_symbol(symbol) for symbol in symbol_table.symbols],
            )
        ],
    )

    stringify.assert_compares_against_dict(result, symbol_table)
    return result


Dumpable = Union[
    Argument,
    AtomicTypeAnnotation,
    Class,
    Constructor,
    Contract,
    Contracts,
    Default,
    Enumeration,
    EnumerationLiteral,
    Interface,
    Method,
    Property,
    SelfTypeAnnotation,
    Signature,
    Snapshot,
    SubscriptedTypeAnnotation,
    Symbol,
    SymbolTable,
    TypeAnnotation,
]


def dump(dumpable: Dumpable) -> str:
    """Produce a string representation of the ``dumpable`` for testing or debugging."""
    stringified = None  # type: Optional[stringify.Entity]

    if isinstance(dumpable, Argument):
        stringified = _stringify_argument(dumpable)
    elif isinstance(dumpable, Class):
        stringified = _stringify_class(dumpable)
    elif isinstance(dumpable, Constructor):
        stringified = _stringify_constructor(dumpable)
    elif isinstance(dumpable, Contract):
        stringified = _stringify_contract(dumpable)
    elif isinstance(dumpable, Contracts):
        stringified = _stringify_contracts(dumpable)
    elif isinstance(dumpable, Default):
        stringified = _stringify_default(dumpable)
    elif isinstance(dumpable, Enumeration):
        stringified = _stringify_enumeration(dumpable)
    elif isinstance(dumpable, EnumerationLiteral):
        stringified = _stringify_enumeration_literal(dumpable)
    elif isinstance(dumpable, Interface):
        stringified = _stringify_interface(dumpable)
    elif isinstance(dumpable, Method):
        stringified = _stringify_method(dumpable)
    elif isinstance(dumpable, Property):
        stringified = _stringify_property(dumpable)
    elif isinstance(dumpable, Signature):
        stringified = _stringify_signature(dumpable)
    elif isinstance(dumpable, Snapshot):
        stringified = _stringify_snapshot(dumpable)
    elif isinstance(dumpable, (Interface, Enumeration, Class)):
        stringified = _stringify_symbol(dumpable)
    elif isinstance(dumpable, SymbolTable):
        stringified = _stringify_symbol_table(dumpable)
    elif isinstance(
            dumpable,
            (AtomicTypeAnnotation, SubscriptedTypeAnnotation, SelfTypeAnnotation)
    ):
        stringified = _stringify_type_annotation(dumpable)
    else:
        assert_never(dumpable)

    assert stringified is not None

    assert isinstance(stringified, stringify.Entity)
    return stringify.dump(stringified)
