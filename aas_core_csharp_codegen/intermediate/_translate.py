"""Translate the parsed representation into the intermediate representation."""
import itertools
from typing import Sequence, List, Mapping, Optional, MutableMapping, Tuple

import asttokens
from icontract import require, ensure

import aas_core_csharp_codegen.understand.constructor as understand_constructor
import aas_core_csharp_codegen.understand.hierarchy as understand_hierarchy
from aas_core_csharp_codegen import parse
from aas_core_csharp_codegen.common import Error, Identifier, assert_never
from aas_core_csharp_codegen.intermediate._types import (
    SymbolTable,
    Enumeration,
    EnumerationLiteral,
    TypeAnnotation,
    AtomicTypeAnnotation,
    SelfTypeAnnotation,
    Argument,
    Default,
    Interface,
    Signature,
    Property,
    Contracts,
    Contract,
    Snapshot,
    Method,
    Class,
    Constructor,
    Symbol, ListTypeAnnotation, SequenceTypeAnnotation, SetTypeAnnotation,
    MappingTypeAnnotation, MutableMappingTypeAnnotation, OptionalTypeAnnotation,
)


def _parsed_enumeration_to_enumeration(parsed: parse.Enumeration) -> Enumeration:
    """Translate an enumeration from the meta-model to an intermediate enumeration."""
    return Enumeration(
        name=parsed.name,
        literals=[
            EnumerationLiteral(
                name=parsed_literal.name,
                value=parsed_literal.value,
                description=parsed_literal.description,
                parsed=parsed_literal,
            )
            for parsed_literal in parsed.literals
        ],
        description=parsed.description,
        parsed=parsed,
    )


def _parsed_type_annotation_to_annotation(
    parsed: parse.TypeAnnotation,
) -> TypeAnnotation:
    """Translate the parsed type annotation into the intermediate one."""
    if isinstance(parsed, parse.AtomicTypeAnnotation):
        return AtomicTypeAnnotation(identifier=parsed.identifier, parsed=parsed)

    elif isinstance(parsed, parse.SubscriptedTypeAnnotation):
        if parsed.identifier == 'Final':
            raise AssertionError(
                "Unexpected ``Final`` type annotation at this stage. "
                "This type annotation should have been processed before.")
            
        elif parsed.identifier == 'List':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the List type annotation, "
                f"but got: {parsed}; this should have been caught before!")
            
            return ListTypeAnnotation(
                items=_parsed_type_annotation_to_annotation(parsed.subscripts[0]),
                parsed=parsed)

        elif parsed.identifier == 'Sequence':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Sequence type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return SequenceTypeAnnotation(
                items=_parsed_type_annotation_to_annotation(parsed.subscripts[0]),
                parsed=parsed)

        elif parsed.identifier == 'Set':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Set type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return SetTypeAnnotation(
                items=_parsed_type_annotation_to_annotation(parsed.subscripts[0]),
                parsed=parsed)
        
        elif parsed.identifier == 'Mapping':
            assert len(parsed.subscripts) == 2, (
                f"Expected exactly two subscripts for the Mapping type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return MappingTypeAnnotation(
                keys=_parsed_type_annotation_to_annotation(parsed.subscripts[0]),
                values=_parsed_type_annotation_to_annotation(parsed.subscripts[1]),
                parsed=parsed)

        elif parsed.identifier == 'MutableMapping':
            assert len(parsed.subscripts) == 2, (
                f"Expected exactly two subscripts "
                f"for the MutableMapping type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return MutableMappingTypeAnnotation(
                keys=_parsed_type_annotation_to_annotation(parsed.subscripts[0]),
                values=_parsed_type_annotation_to_annotation(parsed.subscripts[1]),
                parsed=parsed)

        elif parsed.identifier == 'Optional':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Optional type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return OptionalTypeAnnotation(
                value=_parsed_type_annotation_to_annotation(parsed.subscripts[0]),
                parsed=parsed)

        else:
            raise AssertionError(
                f"Unexpected subscripted type annotation identifier: "
                f"{parsed.identifier}. "
                f"This should have been handled or caught before!")

    elif isinstance(parsed, parse.SelfTypeAnnotation):
        return SelfTypeAnnotation()

    else:
        assert_never(parsed)
        raise AssertionError(parsed)


def _parsed_arguments_to_arguments(parsed: Sequence[parse.Argument]) -> List[Argument]:
    """Translate the arguments of a method in meta-model to the intermediate ones."""
    return [
        Argument(
            name=parsed_arg.name,
            type_annotation=_parsed_type_annotation_to_annotation(
                parsed_arg.type_annotation
            ),
            default=Default(value=parsed_arg.default.value, parsed=parsed_arg.default)
            if parsed_arg.default is not None
            else None,
            parsed=parsed_arg,
        )
        for parsed_arg in parsed
    ]


def _parsed_abstract_entity_to_interface(parsed: parse.AbstractEntity) -> Interface:
    """Translate an abstract entity of a meta-model to an intermediate interface."""
    # noinspection PyTypeChecker
    return Interface(
        name=parsed.name,
        inheritances=parsed.inheritances,
        signatures=[
            Signature(
                name=parsed_method.name,
                arguments=_parsed_arguments_to_arguments(
                    parsed=parsed_method.arguments
                ),
                returns=(
                    None
                    if parsed_method.returns is None
                    else _parsed_type_annotation_to_annotation(parsed_method.returns)
                ),
                description=parsed_method.description,
                parsed=parsed_method,
            )
            for parsed_method in parsed.methods
            if parsed_method.name != "__init__"
        ],
        properties=[
            _parsed_property_to_property(parsed_prop)
            for parsed_prop in parsed.properties
        ],
        is_implementation_specific=parsed.is_implementation_specific,
        parsed=parsed,
    )


def _parsed_property_to_property(parsed: parse.Property) -> Property:
    """Translate a parsed property of a class to an intermediate one."""
    return Property(
        name=parsed.name,
        type_annotation=_parsed_type_annotation_to_annotation(parsed.type_annotation),
        description=parsed.description,
        is_readonly=parsed.is_readonly,
        parsed=parsed,
    )


def _parsed_contracts_to_contracts(parsed: parse.Contracts) -> Contracts:
    """Translate the parsed contracts into intermediate ones."""
    return Contracts(
        preconditions=[
            Contract(
                args=parsed_pre.args,
                description=parsed_pre.description,
                body=parsed_pre.body,
                parsed=parsed_pre,
            )
            for parsed_pre in parsed.preconditions
        ],
        snapshots=[
            Snapshot(
                args=parsed_snap.args,
                body=parsed_snap.body,
                name=parsed_snap.name,
                parsed=parsed_snap,
            )
            for parsed_snap in parsed.snapshots
        ],
        postconditions=[
            Contract(
                args=parsed_post.args,
                description=parsed_post.description,
                body=parsed_post.body,
                parsed=parsed_post,
            )
            for parsed_post in parsed.postconditions
        ],
    )


# fmt: off
@require(
    lambda parsed:
    parsed.name != "__init__",
    "Constructors are expected to be handled in a special way"
)
# fmt: on
def _parsed_method_to_method(parsed: parse.Method) -> Method:
    """Translate the parsed method into an intermediate representation."""
    return Method(
        name=parsed.name,
        is_implementation_specific=parsed.is_implementation_specific,
        arguments=_parsed_arguments_to_arguments(parsed.arguments),
        returns=(
            None
            if parsed.returns is None
            else _parsed_type_annotation_to_annotation(parsed.returns)
        ),
        description=parsed.description,
        contracts=_parsed_contracts_to_contracts(parsed.contracts),
        body=parsed.body,
        parsed=parsed,
    )


def _in_line_constructors(
    parsed_symbol_table: parse.SymbolTable,
    ontology: understand_hierarchy.Ontology,
    constructor_table: understand_constructor.ConstructorTable,
) -> Mapping[parse.Entity, Sequence[understand_constructor.AssignProperty]]:
    """In-line recursively all the constructor bodies."""
    result = (
        dict()
    )  # type: MutableMapping[parse.Entity, List[understand_constructor.AssignProperty]]

    for entity in ontology.entities:
        # We explicitly check at the stage of understand.constructor that all the calls
        # are calls to constructors of a super class or property assignments.

        constructor_body = constructor_table.must_find(entity)
        in_lined = []  # type: List[understand_constructor.AssignProperty]
        for statement in constructor_body:
            if isinstance(statement, understand_constructor.AssignProperty):
                in_lined.append(statement)
            elif isinstance(statement, understand_constructor.CallSuperConstructor):
                antecedent = parsed_symbol_table.must_find_entity(statement.super_name)

                in_lined_of_antecedent = result.get(antecedent, None)

                assert in_lined_of_antecedent is not None, (
                    f"Expected all the constructors of the antecedents "
                    f"of the entity {entity.name} to have been in-lined before "
                    f"due to the topological order of entities in the ontology, "
                    f"but the antecedent {antecedent.name} has not had its "
                    f"constructor in-lined yet"
                )

                in_lined.extend(in_lined_of_antecedent)
            else:
                assert_never(statement)

        assert entity not in result, (
            f"Expected the entity {entity} not to be inserted into the registry of "
            f"in-lined constructors since its in-lined constructor "
            f"has just been computed."
        )

        result[entity] = in_lined

    return result


def _stack_contracts(contracts: Contracts, other: Contracts) -> Contracts:
    """Join the two contracts together."""
    return Contracts(
        preconditions=list(
            itertools.chain(contracts.preconditions, other.preconditions)
        ),
        snapshots=list(itertools.chain(contracts.snapshots, other.snapshots)),
        postconditions=list(
            itertools.chain(contracts.postconditions, other.postconditions)
        ),
    )


def _parsed_entity_to_class(
    parsed: parse.ConcreteEntity,
    ontology: understand_hierarchy.Ontology,
    in_lined_constructors: Mapping[
        parse.Entity, Sequence[understand_constructor.AssignProperty]
    ],
) -> Class:
    """Translate a concrete entity to an intermediate class."""
    antecedents = ontology.list_antecedents(entity=parsed)

    # region Stack properties from the antecedents

    properties = []  # type: List[Property]

    # We explicitly check that there are no property overloads at the parse stage so
    # we do not perform the same check here for the second time.

    for antecedent in antecedents:
        properties.extend(
            _parsed_property_to_property(parsed_prop)
            for parsed_prop in antecedent.properties
        )

    for parsed_prop in parsed.properties:
        properties.append(_parsed_property_to_property(parsed_prop))

    # endregion

    # region Stack constructors from the antecedents

    contracts = Contracts(preconditions=[], snapshots=[], postconditions=[])

    for antecedent in antecedents:
        parsed_antecedent_init = antecedent.method_map.get(Identifier("__init__"), None)

        if parsed_antecedent_init is not None:
            contracts = _stack_contracts(
                contracts,
                _parsed_contracts_to_contracts(parsed_antecedent_init.contracts),
            )

    arguments = []
    is_implementation_specific = False

    parsed_entity_init = parsed.method_map.get(Identifier("__init__"), None)
    if parsed_entity_init is not None:
        arguments = _parsed_arguments_to_arguments(parsed_entity_init.arguments)
        is_implementation_specific = parsed_entity_init.is_implementation_specific
        contracts = _stack_contracts(
            contracts, _parsed_contracts_to_contracts(parsed_entity_init.contracts)
        )

    constructor = Constructor(
        arguments=arguments,
        contracts=contracts,
        is_implementation_specific=is_implementation_specific,
        statements=in_lined_constructors[parsed],
    )

    # endregion

    # region Stack methods from the antecedents

    methods = []  # type: List[Method]

    # We explicitly check that there are no method overloads at the parse stage
    # so we do not perform this check for the second time here.

    for antecedent in antecedents:
        methods.extend(
            _parsed_method_to_method(parsed_method)
            for parsed_method in antecedent.methods
            if parsed_method.name != "__init__"
        )

    for parsed_method in parsed.methods:
        if parsed_method.name == "__init__":
            # Constructors are in-lined and handled in a different way through
            # :py:class:`Constructors`.
            continue

        methods.append(_parsed_method_to_method(parsed_method))

    # endregion

    return Class(
        name=parsed.name,
        interfaces=parsed.inheritances,
        is_implementation_specific=parsed.is_implementation_specific,
        properties=properties,
        methods=methods,
        constructor=constructor,
        description=parsed.description,
        parsed=parsed,
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def translate(
    parsed_symbol_table: parse.SymbolTable,
    ontology: understand_hierarchy.Ontology,
    constructor_table: understand_constructor.ConstructorTable,
    atok: asttokens.ASTTokens,
) -> Tuple[Optional[SymbolTable], Optional[Error]]:
    """Translate the parsed symbols into intermediate symbols."""
    underlying_errors = []  # type: List[Error]

    in_lined_constructors = _in_line_constructors(
        parsed_symbol_table=parsed_symbol_table,
        ontology=ontology,
        constructor_table=constructor_table,
    )

    symbols = []  # type: List[Symbol]
    for parsed_symbol in parsed_symbol_table.symbols:
        symbol = None  # type: Optional[Symbol]

        if isinstance(parsed_symbol, parse.Enumeration):
            symbol = _parsed_enumeration_to_enumeration(parsed=parsed_symbol)

        elif isinstance(parsed_symbol, parse.AbstractEntity):
            symbol = _parsed_abstract_entity_to_interface(parsed=parsed_symbol)

        elif isinstance(parsed_symbol, parse.ConcreteEntity):
            symbol = _parsed_entity_to_class(
                parsed=parsed_symbol,
                ontology=ontology,
                in_lined_constructors=in_lined_constructors,
            )

        else:
            assert_never(parsed_symbol)

        assert symbol is not None
        symbols.append(symbol)

    if len(underlying_errors) > 0:
        return (
            None,
            Error(
                atok.tree,
                "Failed to translate the parsed symbol table "
                "to an intermediate symbol table",
                underlying=underlying_errors,
            ),
        )

    symbol_table = SymbolTable(symbols=symbols)
    return symbol_table, None
