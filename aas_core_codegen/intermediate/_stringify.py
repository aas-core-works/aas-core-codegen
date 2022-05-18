"""Stringify the intermediate representation."""

from typing import Union, Optional

from aas_core_codegen import stringify
from aas_core_codegen.intermediate import _types, construction
from aas_core_codegen.intermediate._types import (
    AbstractClass,
    Argument,
    Class,
    ConcreteClass,
    ConstrainedPrimitive,
    Constructor,
    Contract,
    Contracts,
    Default,
    DefaultConstant,
    DefaultEnumerationLiteral,
    Enumeration,
    EnumerationLiteral,
    ImplementationSpecificMethod,
    ImplementationSpecificVerification,
    Interface,
    Invariant,
    ListTypeAnnotation,
    MetaModel,
    OptionalTypeAnnotation,
    OurTypeAnnotation,
    PatternVerification,
    PrimitiveTypeAnnotation,
    Property,
    Serialization,
    Signature,
    Snapshot,
    Symbol,
    SymbolTable,
    UnderstoodMethod,
    ReferenceInTheBook,
    MetaModelDescription,
    SymbolDescription,
    SignatureDescription,
    PropertyDescription,
    EnumerationLiteralDescription,
    SignatureLike,
)
from aas_core_codegen.parse import tree as parse_tree


def _stringify_primitive_type_annotation(
    that: PrimitiveTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("a_type", that.a_type.name),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_our_type_annotation(
    that: OurTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("symbol", f"Reference to symbol {that.symbol.name}"),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_list_type_annotation(
    that: ListTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("items", _stringify(that.items)),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_optional_type_annotation(
    that: OptionalTypeAnnotation,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("value", _stringify(that.value)),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_meta_model_description(
    that: MetaModelDescription,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("summary", str(that.summary)),
            stringify.Property("remarks", list(map(str, that.remarks))),
            stringify.Property(
                "constraints_by_identifier",
                [
                    [identifier, str(body)]
                    for identifier, body in that.constraints_by_identifier.items()
                ],
            ),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_symbol_description(
    that: SymbolDescription,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("summary", str(that.summary)),
            stringify.Property("remarks", list(map(str, that.remarks))),
            stringify.Property(
                "constraints_by_identifier",
                [
                    [identifier, str(body)]
                    for identifier, body in that.constraints_by_identifier.items()
                ],
            ),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_property_description(
    that: PropertyDescription,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("summary", str(that.summary)),
            stringify.Property("remarks", list(map(str, that.remarks))),
            stringify.Property(
                "constraints_by_identifier",
                [
                    [identifier, str(body)]
                    for identifier, body in that.constraints_by_identifier.items()
                ],
            ),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_enumeration_literal_description(
    that: EnumerationLiteralDescription,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("summary", str(that.summary)),
            stringify.Property("remarks", list(map(str, that.remarks))),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_signature_description(
    that: SignatureDescription,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("summary", str(that.summary)),
            stringify.Property("remarks", list(map(str, that.remarks))),
            stringify.Property(
                "arguments_by_name",
                [[name, str(body)] for name, body in that.arguments_by_name.items()],
            ),
            stringify.Property(
                "returns", None if that.returns is None else str(that.returns)
            ),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_property(
    that: Property,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("type_annotation", _stringify(that.type_annotation)),
            stringify.Property("description", _stringify(that.description)),
            stringify.Property(
                "specified_for",
                f"Reference to {that.specified_for.__class__.__name__} "
                f"{that.specified_for.name}",
            ),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_default_constant(
    that: DefaultConstant,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("value", that.value),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_default_enumeration_literal(
    that: DefaultEnumerationLiteral,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property(
                "enumeration",
                f"Reference to {that.enumeration.__class__.__name__} "
                f"{that.enumeration.name}",
            ),
            stringify.Property(
                "literal",
                f"Reference to {that.literal.__class__.__name__} "
                f"{that.literal.name}",
            ),
        ],
    )

    return result


def _stringify_argument(
    that: Argument,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("type_annotation", _stringify(that.type_annotation)),
            stringify.Property("default", _stringify(that.default)),
            stringify.PropertyEllipsis("parsed", that.parsed),
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


def _stringify_reference_in_the_book(
    that: ReferenceInTheBook,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("section", list(that.section)),
            stringify.Property("index", that.index),
            stringify.Property("fragment", that.fragment),
        ],
    )

    return result


def _stringify_invariant(
    that: Invariant,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("description", that.description),
            stringify.Property("body", parse_tree.dump(that.body)),
            stringify.Property(
                "specified_for",
                f"Reference to {that.specified_for.__class__.__name__} "
                f"{that.specified_for.name}",
            ),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_contract(
    that: Contract,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("args", that.args),
            stringify.Property("description", that.description),
            stringify.Property("body", parse_tree.dump(that.body)),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_snapshot(
    that: Snapshot,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("args", that.args),
            stringify.Property("body", parse_tree.dump(that.body)),
            stringify.Property("name", that.name),
            stringify.PropertyEllipsis("parsed", that.parsed),
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


def _stringify_a_signature_like(that: SignatureLike) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("arguments", list(map(_stringify, that.arguments))),
            stringify.Property("returns", _stringify(that.returns)),
            stringify.Property("description", _stringify(that.description)),
            stringify.Property("contracts", _stringify(that.contracts)),
            stringify.PropertyEllipsis("parsed", that.parsed),
            stringify.PropertyEllipsis("arguments_by_name", that.arguments_by_name),
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
            stringify.Property("arguments", list(map(_stringify, that.arguments))),
            stringify.Property("returns", _stringify(that.returns)),
            stringify.Property("description", _stringify(that.description)),
            stringify.Property(
                "specified_for",
                f"Reference to {that.specified_for.__class__.__name__} "
                f"{that.specified_for.name}",
            ),
            stringify.Property("contracts", _stringify(that.contracts)),
            stringify.PropertyEllipsis("parsed", that.parsed),
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
            stringify.Property("arguments", list(map(_stringify, that.arguments))),
            stringify.Property("returns", _stringify(that.returns)),
            stringify.Property("description", _stringify(that.description)),
            stringify.Property(
                "specified_for",
                f"Reference to {that.specified_for.__class__.__name__} "
                f"{that.specified_for.name}",
            ),
            stringify.Property("contracts", _stringify(that.contracts)),
            stringify.PropertyEllipsis("parsed", that.parsed),
            stringify.Property("body", [parse_tree.dump(stmt) for stmt in that.body]),
            stringify.PropertyEllipsis("arguments_by_name", that.arguments_by_name),
        ],
    )

    return result


def _stringify_constructor(
    that: Constructor,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("arguments", list(map(_stringify, that.arguments))),
            stringify.Property("returns", _stringify(that.returns)),
            stringify.Property("description", _stringify(that.description)),
            stringify.Property("contracts", _stringify(that.contracts)),
            stringify.PropertyEllipsis("parsed", that.parsed),
            stringify.PropertyEllipsis("arguments_by_name", that.arguments_by_name),
            stringify.Property(
                "is_implementation_specific", that.is_implementation_specific
            ),
            stringify.Property(
                "statements", list(map(construction.dump, that.statements))
            ),
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
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_enumeration(
    that: Enumeration,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property("literals", list(map(_stringify, that.literals))),
            stringify.Property(
                "is_superset_of",
                [
                    f"Reference to {parent_enum.__class__.__name__} "
                    f"{parent_enum.name}"
                    for parent_enum in that.is_superset_of
                ],
            ),
            stringify.Property(
                "reference_in_the_book", _stringify(that.reference_in_the_book)
            ),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("literals_by_name", that.literals_by_name),
            stringify.PropertyEllipsis("literal_id_set", that.literal_id_set),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_constrained_primitive(
    that: ConstrainedPrimitive,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property(
                "inheritances",
                [
                    f"Reference to {inheritance.__class__.__name__} {inheritance.name}"
                    for inheritance in that.inheritances
                ],
            ),
            stringify.PropertyEllipsis("inheritance_id_set", that.inheritance_id_set),
            stringify.PropertyEllipsis("descendant_id_set", that.descendant_id_set),
            stringify.Property("constrainee", that.constrainee.name),
            stringify.Property(
                "is_implementation_specific", that.is_implementation_specific
            ),
            stringify.Property("invariants", list(map(_stringify, that.invariants))),
            stringify.PropertyEllipsis("invariant_id_set", that.invariant_id_set),
            stringify.Property(
                "reference_in_the_book", _stringify(that.reference_in_the_book)
            ),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("parsed", that.parsed),
        ],
    )

    return result


def _stringify_a_class(that: Class) -> stringify.Entity:
    # NOTE (mristin, 2021-12-26):
    # Concrete and abstract class share all the attributes, so we provide a single
    # stringification function.

    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("name", that.name),
            stringify.Property(
                "inheritances",
                [
                    f"Reference to {inheritance.__class__.__name__} {inheritance.name}"
                    for inheritance in that.inheritances
                ],
            ),
            stringify.PropertyEllipsis("inheritance_id_set", that.inheritance_id_set),
            stringify.Property(
                "is_implementation_specific", that.is_implementation_specific
            ),
            stringify.Property("interface", _stringify(that.interface)),
            stringify.PropertyEllipsis("descendant_id_set", that.descendant_id_set),
            stringify.Property(
                "concrete_descendants",
                [
                    f"Reference to {descendant.__class__.__name__} {descendant.name}"
                    for descendant in that.concrete_descendants
                ],
            ),
            stringify.Property("properties", list(map(_stringify, that.properties))),
            stringify.Property("methods", list(map(_stringify, that.methods))),
            stringify.Property("constructor", _stringify(that.constructor)),
            stringify.Property("invariants", list(map(_stringify, that.invariants))),
            stringify.Property("serialization", _stringify(that.serialization)),
            stringify.Property(
                "reference_in_the_book", _stringify(that.reference_in_the_book)
            ),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("parsed", that.parsed),
            stringify.PropertyEllipsis("properties_by_name", that.properties_by_name),
            stringify.PropertyEllipsis("property_id_set", that.property_id_set),
            stringify.PropertyEllipsis("methods_by_name", that.methods_by_name),
            stringify.PropertyEllipsis("invariant_id_set", that.invariant_id_set),
        ],
    )

    return result


def _stringify_concrete_class(that: ConcreteClass) -> stringify.Entity:
    return _stringify_a_class(that)


def _stringify_abstract_class(that: AbstractClass) -> stringify.Entity:
    return _stringify_a_class(that)


def _stringify_implementation_specific_verification(
    that: ImplementationSpecificVerification,
) -> stringify.Entity:
    return _stringify_a_signature_like(that)


def _stringify_pattern_verification(
    that: PatternVerification,
) -> stringify.Entity:
    signature_like = _stringify_a_signature_like(that)

    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=list(signature_like.properties)
        + [stringify.Property("pattern", that.pattern)],
    )

    return result


def _stringify_signature(
    that: Signature,
) -> stringify.Entity:
    return _stringify_a_signature_like(that)


def _stringify_interface(
    that: Interface,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property(
                "base",
                f"Reference to {that.base.__class__.__name__} " f"{that.base.name}",
            ),
            stringify.Property("name", that.name),
            stringify.Property(
                "inheritances",
                [
                    f"Reference to {inheritance.__class__.__name__} {inheritance.name}"
                    for inheritance in that.inheritances
                ],
            ),
            stringify.Property(
                "implementers",
                [
                    f"Reference to {implementer.__class__.__name__} {implementer.name}"
                    for implementer in that.implementers
                ],
            ),
            stringify.Property("properties", list(map(_stringify, that.properties))),
            stringify.Property("signatures", list(map(_stringify, that.signatures))),
            stringify.Property("description", _stringify(that.description)),
            stringify.PropertyEllipsis("parsed", that.parsed),
            stringify.PropertyEllipsis("properties_by_name", that.properties_by_name),
            stringify.PropertyEllipsis("property_id_set", that.property_id_set),
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


def _stringify_symbol_table(
    that: SymbolTable,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("symbols", list(map(_stringify, that.symbols))),
            stringify.Property(
                "symbols_topologically_sorted",
                [
                    f"Reference to symbol {symbol.name}"
                    for symbol in that.symbols_topologically_sorted
                ],
            ),
            stringify.Property(
                "verification_functions",
                list(map(_stringify, that.verification_functions)),
            ),
            stringify.PropertyEllipsis(
                "verification_functions_by_name", that.verification_functions_by_name
            ),
            stringify.Property("meta_model", _stringify(that.meta_model)),
        ],
    )

    return result


Dumpable = Union[
    AbstractClass,
    Argument,
    ConcreteClass,
    Constructor,
    Contract,
    Contracts,
    Default,
    MetaModelDescription,
    SymbolDescription,
    PropertyDescription,
    EnumerationLiteralDescription,
    SignatureDescription,
    Enumeration,
    EnumerationLiteral,
    ImplementationSpecificMethod,
    ImplementationSpecificVerification,
    Interface,
    Invariant,
    ListTypeAnnotation,
    MetaModel,
    OptionalTypeAnnotation,
    OurTypeAnnotation,
    PatternVerification,
    PrimitiveTypeAnnotation,
    Property,
    ReferenceInTheBook,
    Serialization,
    Signature,
    Snapshot,
    Symbol,
    SymbolTable,
    UnderstoodMethod,
]

stringify.assert_all_public_types_listed_as_dumpables(
    dumpable=Dumpable, types_module=_types
)

_DISPATCH = {
    AbstractClass: _stringify_abstract_class,
    Argument: _stringify_argument,
    ConcreteClass: _stringify_concrete_class,
    ConstrainedPrimitive: _stringify_constrained_primitive,
    Constructor: _stringify_constructor,
    Contract: _stringify_contract,
    Contracts: _stringify_contracts,
    DefaultConstant: _stringify_default_constant,
    DefaultEnumerationLiteral: _stringify_default_enumeration_literal,
    MetaModelDescription: _stringify_meta_model_description,
    SymbolDescription: _stringify_symbol_description,
    PropertyDescription: _stringify_property_description,
    EnumerationLiteralDescription: _stringify_enumeration_literal_description,
    SignatureDescription: _stringify_signature_description,
    Enumeration: _stringify_enumeration,
    EnumerationLiteral: _stringify_enumeration_literal,
    ImplementationSpecificMethod: _stringify_implementation_specific_method,
    ImplementationSpecificVerification: _stringify_implementation_specific_verification,
    Interface: _stringify_interface,
    Invariant: _stringify_invariant,
    ListTypeAnnotation: _stringify_list_type_annotation,
    MetaModel: _stringify_meta_model,
    OptionalTypeAnnotation: _stringify_optional_type_annotation,
    OurTypeAnnotation: _stringify_our_type_annotation,
    PatternVerification: _stringify_pattern_verification,
    PrimitiveTypeAnnotation: _stringify_primitive_type_annotation,
    Property: _stringify_property,
    ReferenceInTheBook: _stringify_reference_in_the_book,
    Serialization: _stringify_serialization,
    Signature: _stringify_signature,
    Snapshot: _stringify_snapshot,
    SymbolTable: _stringify_symbol_table,
    UnderstoodMethod: _stringify_understood_method,
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
