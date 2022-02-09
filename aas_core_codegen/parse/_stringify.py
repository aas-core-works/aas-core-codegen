"""Stringify the parsed meta-model."""
from typing import Optional, Union

from aas_core_codegen import stringify
from aas_core_codegen.parse import _types
from aas_core_codegen.parse import tree
from aas_core_codegen.parse._types import (
    AbstractClass,
    Argument,
    AtomicTypeAnnotation,
    ConcreteClass,
    Contract,
    Contracts,
    Default,
    Class,
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
    UnverifiedSymbolTable,
    Description,
    Invariant,
    ImplementationSpecificMethod,
    UnderstoodMethod,
    ConstructorToBeUnderstood,
    Serialization,
    MetaModel,
)


def _stringify_atomic_type_annotation(
    that: AtomicTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("identifier", that.identifier),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )

    return result


def _stringify_self_type_annotation(
    that: SelfTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[],
    )

    return result


def _stringify_subscripted_type_annotation(
    that: SubscriptedTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("identifier", that.identifier),
            stringify.Property("subscripts", list(map(_stringify, that.subscripts))),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )

    return result


def _stringify_description(that: Description) -> stringify.Entity:
    return stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.PropertyEllipsis("document", that.document),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )


def _stringify_property(that: Property) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("type_annotation", _stringify(that.type_annotation)),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )

    return result


def _stringify_default(that: Default) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[stringify.PropertyEllipsis("node", that.node)],
    )

    return result


def _stringify_argument(that: Argument) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("type_annotation", _stringify(that.type_annotation)),
            stringify.Property(
                "default",
                _stringify(that.default),
            ),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )

    return result


def _stringify_invariant(that: Invariant) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("description", that.description),
            stringify.Property("body", tree.dump(that.body)),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )

    return result


def _stringify_contract(that: Contract) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("args", that.args),
            stringify.Property("description", that.description),
            stringify.PropertyEllipsis("body", tree.dump(that.body)),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )

    return result


def _stringify_snapshot(that: Snapshot) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("args", that.args),
            stringify.Property("name", that.name),
            stringify.Property("body", tree.dump(that.body)),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )

    return result


def _stringify_contracts(that: Contracts) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property(
                "preconditions", list(map(_stringify, that.preconditions))
            ),
            stringify.Property("snapshots", list(map(_stringify, that.snapshots))),
            stringify.Property(
                "postconditions",
                list(map(_stringify, that.postconditions)),
            ),
        ],
    )

    return result


def _stringify_implementation_specific_method(
    that: ImplementationSpecificMethod,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("verification", that.verification),
            stringify.Property("arguments", list(map(_stringify, that.arguments))),
            stringify.Property("returns", _stringify(that.returns)),
            stringify.Property("description", _stringify(that.description)),
            stringify.Property("contracts", _stringify(that.contracts)),
            stringify.PropertyEllipsis("node", that.node),
            stringify.PropertyEllipsis("arguments_by_name", that.arguments_by_name),
        ],
    )

    return result


def _stringify_understood_method(
    that: UnderstoodMethod,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("verification", that.verification),
            stringify.Property("arguments", list(map(_stringify, that.arguments))),
            stringify.Property("returns", _stringify(that.returns)),
            stringify.Property("description", _stringify(that.description)),
            stringify.Property("contracts", _stringify(that.contracts)),
            stringify.Property("body", list(map(tree.dump, that.body))),
            stringify.PropertyEllipsis("node", that.node),
            stringify.PropertyEllipsis("arguments_by_name", that.arguments_by_name),
        ],
    )

    return result


def _stringify_constructor_to_be_understood(
    that: ConstructorToBeUnderstood,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("verification", that.verification),
            stringify.Property("arguments", list(map(_stringify, that.arguments))),
            stringify.Property("returns", _stringify(that.returns)),
            stringify.Property("description", _stringify(that.description)),
            stringify.Property("contracts", _stringify(that.contracts)),
            stringify.PropertyEllipsis("node", that.node),
            stringify.PropertyEllipsis("arguments_by_name", that.arguments_by_name),
            stringify.PropertyEllipsis("body", that.body),
        ],
    )

    return result


def _stringify_serialization(
    that: Serialization,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("with_model_type", that.with_model_type),
        ],
    )

    return result


def _stringify_abstract_class(that: AbstractClass) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property(
                "is_implementation_specific", that.is_implementation_specific
            ),
            stringify.Property("inheritances", that.inheritances),
            stringify.Property("properties", list(map(_stringify, that.properties))),
            stringify.Property("methods", list(map(_stringify, that.methods))),
            stringify.Property("invariants", list(map(_stringify, that.invariants))),
            stringify.Property("serialization", _stringify(that.serialization)),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("node", that.node),
            stringify.PropertyEllipsis("properties_by_name", that.properties_by_name),
            stringify.PropertyEllipsis("methods_by_name", that.methods_by_name),
        ],
    )

    return result


def _stringify_concrete_class(that: ConcreteClass) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property(
                "is_implementation_specific", that.is_implementation_specific
            ),
            stringify.Property("inheritances", that.inheritances),
            stringify.Property("properties", list(map(_stringify, that.properties))),
            stringify.Property("methods", list(map(_stringify, that.methods))),
            stringify.Property("invariants", list(map(_stringify, that.invariants))),
            stringify.Property("serialization", _stringify(that.serialization)),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("node", that.node),
            stringify.PropertyEllipsis("properties_by_name", that.properties_by_name),
            stringify.PropertyEllipsis("methods_by_name", that.methods_by_name),
        ],
    )

    return result


def _stringify_enumeration_literal(
    that: EnumerationLiteral,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("value", that.value),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("node", that.node),
        ],
    )

    return result


def _stringify_enumeration(that: Enumeration) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("is_superset_of", that.is_superset_of),
            stringify.Property("literals", list(map(_stringify, that.literals))),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("node", that.node),
            stringify.PropertyEllipsis("literals_by_name", that.literals_by_name),
        ],
    )

    return result


def _stringify_meta_model(
    that: MetaModel,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("description", _stringify(that.description)),
            stringify.Property("book_url", that.book_url),
            stringify.Property("book_version", that.book_version),
        ],
    )

    return result


def _stringify_unverified_symbol_table(
    that: UnverifiedSymbolTable,
) -> stringify.Entity:
    entity = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("symbols", list(map(_stringify, that.symbols))),
            stringify.Property(
                "verification_functions",
                list(map(_stringify, that.verification_functions)),
            ),
            stringify.Property("meta_model", _stringify(that.meta_model)),
        ],
    )

    return entity


def _stringify_symbol_table(that: SymbolTable) -> stringify.Entity:
    entity = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("symbols", list(map(_stringify, that.symbols))),
            stringify.Property(
                "verification_functions",
                list(map(_stringify, that.verification_functions)),
            ),
            stringify.Property("meta_model", _stringify(that.meta_model)),
        ],
    )

    return entity


Dumpable = Union[
    Argument,
    AtomicTypeAnnotation,
    Class,
    ConcreteClass,
    ConstructorToBeUnderstood,
    Contract,
    Contracts,
    Default,
    Description,
    Enumeration,
    EnumerationLiteral,
    ImplementationSpecificMethod,
    Invariant,
    MetaModel,
    Method,
    Property,
    SelfTypeAnnotation,
    Serialization,
    Snapshot,
    SubscriptedTypeAnnotation,
    Symbol,
    SymbolTable,
    TypeAnnotation,
    UnderstoodMethod,
    UnverifiedSymbolTable,
]

stringify.assert_all_public_types_listed_as_dumpables(
    dumpable=Dumpable, types_module=_types
)

_DISPATCH = {
    AbstractClass: _stringify_abstract_class,
    Argument: _stringify_argument,
    AtomicTypeAnnotation: _stringify_atomic_type_annotation,
    ConcreteClass: _stringify_concrete_class,
    ConstructorToBeUnderstood: _stringify_constructor_to_be_understood,
    Contract: _stringify_contract,
    Contracts: _stringify_contracts,
    Default: _stringify_default,
    Description: _stringify_description,
    Enumeration: _stringify_enumeration,
    EnumerationLiteral: _stringify_enumeration_literal,
    ImplementationSpecificMethod: _stringify_implementation_specific_method,
    Invariant: _stringify_invariant,
    MetaModel: _stringify_meta_model,
    Property: _stringify_property,
    SelfTypeAnnotation: _stringify_self_type_annotation,
    Serialization: _stringify_serialization,
    Snapshot: _stringify_snapshot,
    SubscriptedTypeAnnotation: _stringify_subscripted_type_annotation,
    SymbolTable: _stringify_symbol_table,
    UnderstoodMethod: _stringify_understood_method,
    UnverifiedSymbolTable: _stringify_unverified_symbol_table,
}

stringify.assert_dispatch_exhaustive(dispatch=_DISPATCH, dumpable=Dumpable)


def _stringify(that: Optional[Dumpable]) -> Optional[stringify.Entity]:
    """Dispatch to the correct ``_stringify_*`` method."""
    if that is None:
        return None

    stringify_func = _DISPATCH.get(that.__class__, None)
    if stringify_func is None:
        raise AssertionError(
            f"No stringify function could be found for the class {that.__class__}"
        )

    stringified = stringify_func(that)  # type: ignore
    assert isinstance(stringified, stringify.Entity)
    stringify.assert_compares_against_dict(stringified, that)

    return stringified


def dump(that: Optional[Dumpable]) -> str:
    """Produce a string representation of the ``dumpable`` for testing or debugging."""
    if that is None:
        return repr(None)

    stringified = _stringify(that)
    return stringify.dump(stringified)
