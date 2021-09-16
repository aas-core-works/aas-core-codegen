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
    OurAtomicTypeAnnotation, STR_TO_BUILTIN_ATOMIC_TYPE, BuiltinAtomicTypeAnnotation,
    Description,
)


def _parsed_description_to_description(parsed: parse.Description) -> Description:
    """Translate the parsed description to an intermediate form."""
    # This function makes a simple copy at the moment, which might seem pointless.
    #
    # However, we want to explicitly delineate layers (the parse and the intermediate
    # layer, respectively). This simple copying thus helps the understanding
    # of the general system and allows the reader to ignore, to a certain degree, the
    # parse layer when examining the output of the intermediate layer.
    return Description(document=parsed.document, node=parsed.node)


def _parsed_enumeration_to_enumeration(
        parsed: parse.Enumeration
) -> Enumeration:
    """Translate an enumeration from the meta-model to an intermediate enumeration."""
    return Enumeration(
        name=parsed.name,
        literals=[
            EnumerationLiteral(
                name=parsed_literal.name,
                value=parsed_literal.value,
                description=_parsed_description_to_description(
                    parsed_literal.description),
                parsed=parsed_literal,
            )
            for parsed_literal in parsed.literals
        ],
        description=_parsed_description_to_description(parsed.description),
        parsed=parsed,
    )


class _PlaceholderSymbol(Symbol):
    """Reference a symbol which will be resolved once the table is built."""

    def __init__(self, identifier: Identifier) -> None:
        self.identifier = identifier


class _FirstPassTypeAnnotator:
    """
    Translate parsed type annotations to temporary type annotation.

    We need a two-pass translation to translate atomic type annotations to
    intermediate ones. Namely, we are translating the type annotations as we are
    building the symbol table. At that point, the atomic type annotations referring to
    meta-model entities can not be resolved (as the symbol table is not completely
    built yet). Therefore, we use placeholders which are eventually resolved in the
    second pass.

    This annotator provides the translations for the first pass, and keeps track of
    all the pending type annotations which need to be resolved in the second pass.
    """

    def __init__(self) -> None:
        # Map ``identifier`` 🠒 unfinished type annotation that needs to be resolved
        # in the second pass
        self.to_be_resolved = dict(
        )  # type: MutableMapping[str, OurAtomicTypeAnnotation]

    def translate(self, parsed: parse.TypeAnnotation) -> TypeAnnotation:
        """Translate the parsed type annotation into the intermediate one."""
        if isinstance(parsed, parse.AtomicTypeAnnotation):
            builtin_atomic_type = STR_TO_BUILTIN_ATOMIC_TYPE.get(
                parsed.identifier, None)

            if builtin_atomic_type is not None:
                return BuiltinAtomicTypeAnnotation(
                    a_type=builtin_atomic_type, parsed=parsed)

            our_type_annotation = self.to_be_resolved.get(parsed.identifier, None)
            if our_type_annotation is None:
                our_type_annotation = OurAtomicTypeAnnotation(
                    symbol=_PlaceholderSymbol(identifier=parsed.identifier),
                    parsed=parsed)

                self.to_be_resolved[parsed.identifier] = our_type_annotation

            return our_type_annotation

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
                    items=self.translate(parsed.subscripts[0]),
                    parsed=parsed)

            elif parsed.identifier == 'Sequence':
                assert len(parsed.subscripts) == 1, (
                    f"Expected exactly one subscript for the Sequence type annotation, "
                    f"but got: {parsed}; this should have been caught before!")

                return SequenceTypeAnnotation(
                    items=self.translate(parsed.subscripts[0]),
                    parsed=parsed)

            elif parsed.identifier == 'Set':
                assert len(parsed.subscripts) == 1, (
                    f"Expected exactly one subscript for the Set type annotation, "
                    f"but got: {parsed}; this should have been caught before!")

                return SetTypeAnnotation(
                    items=self.translate(parsed.subscripts[0]),
                    parsed=parsed)

            elif parsed.identifier == 'Mapping':
                assert len(parsed.subscripts) == 2, (
                    f"Expected exactly two subscripts for the Mapping type annotation, "
                    f"but got: {parsed}; this should have been caught before!")

                return MappingTypeAnnotation(
                    keys=self.translate(parsed.subscripts[0]),
                    values=self.translate(parsed.subscripts[1]),
                    parsed=parsed)

            elif parsed.identifier == 'MutableMapping':
                assert len(parsed.subscripts) == 2, (
                    f"Expected exactly two subscripts "
                    f"for the MutableMapping type annotation, "
                    f"but got: {parsed}; this should have been caught before!")

                return MutableMappingTypeAnnotation(
                    keys=self.translate(parsed.subscripts[0]),
                    values=self.translate(parsed.subscripts[1]),
                    parsed=parsed)

            elif parsed.identifier == 'Optional':
                assert len(parsed.subscripts) == 1, (
                    f"Expected exactly one subscript for the Optional type annotation, "
                    f"but got: {parsed}; this should have been caught before!")

                return OptionalTypeAnnotation(
                    value=self.translate(parsed.subscripts[0]),
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


def _parsed_arguments_to_arguments(
        parsed: Sequence[parse.Argument],
        first_pass_type_annotator: _FirstPassTypeAnnotator
) -> List[Argument]:
    """Translate the arguments of a method in meta-model to the intermediate ones."""
    return [
        Argument(
            name=parsed_arg.name,
            type_annotation=first_pass_type_annotator.translate(
                parsed_arg.type_annotation),
            default=Default(value=parsed_arg.default.value, parsed=parsed_arg.default)
            if parsed_arg.default is not None
            else None,
            parsed=parsed_arg,
        )
        for parsed_arg in parsed
    ]


def _parsed_abstract_entity_to_interface(
        parsed: parse.AbstractEntity,
        first_pass_type_annotator: _FirstPassTypeAnnotator
) -> Interface:
    """Translate an abstract entity of a meta-model to an intermediate interface."""
    # noinspection PyTypeChecker
    return Interface(
        name=parsed.name,
        inheritances=parsed.inheritances,
        signatures=[
            Signature(
                name=parsed_method.name,
                arguments=_parsed_arguments_to_arguments(
                    parsed=parsed_method.arguments,
                    first_pass_type_annotator=first_pass_type_annotator
                ),
                returns=(
                    None
                    if parsed_method.returns is None
                    else first_pass_type_annotator.translate(parsed_method.returns)
                ),
                description=_parsed_description_to_description(
                    parsed_method.description),
                parsed=parsed_method,
            )
            for parsed_method in parsed.methods
            if parsed_method.name != "__init__"
        ],
        properties=[
            _parsed_property_to_property(
                parsed=parsed_prop,
                first_pass_type_annotator=first_pass_type_annotator
            )
            for parsed_prop in parsed.properties
        ],
        is_implementation_specific=parsed.is_implementation_specific,
        description=_parsed_description_to_description(parsed.description),
        parsed=parsed,
    )


def _parsed_property_to_property(
        parsed: parse.Property,
        first_pass_type_annotator: _FirstPassTypeAnnotator
) -> Property:
    """Translate a parsed property of a class to an intermediate one."""
    return Property(
        name=parsed.name,
        type_annotation=first_pass_type_annotator.translate(parsed.type_annotation),
        description=_parsed_description_to_description(parsed.description),
        is_readonly=parsed.is_readonly,
        parsed=parsed,
    )


def _parsed_contracts_to_contracts(parsed: parse.Contracts) -> Contracts:
    """Translate the parsed contracts into intermediate ones."""
    return Contracts(
        preconditions=[
            Contract(
                args=parsed_pre.args,
                description=_parsed_description_to_description(parsed_pre.description),
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
                description=_parsed_description_to_description(parsed_post.description),
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
def _parsed_method_to_method(
        parsed: parse.Method,
        first_pass_type_annotator: _FirstPassTypeAnnotator
) -> Method:
    """Translate the parsed method into an intermediate representation."""
    return Method(
        name=parsed.name,
        is_implementation_specific=parsed.is_implementation_specific,
        arguments=_parsed_arguments_to_arguments(
            parsed=parsed.arguments,
            first_pass_type_annotator=first_pass_type_annotator
        ),
        returns=(
            None
            if parsed.returns is None
            else first_pass_type_annotator.translate(parsed.returns)
        ),
        description=_parsed_description_to_description(parsed.description),
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
        first_pass_type_annotator: _FirstPassTypeAnnotator
) -> Class:
    """Translate a concrete entity to an intermediate class."""
    antecedents = ontology.list_antecedents(entity=parsed)

    # region Stack properties from the antecedents

    properties = []  # type: List[Property]

    # We explicitly check that there are no property overloads at the parse stage so
    # we do not perform the same check here for the second time.

    for antecedent in antecedents:
        properties.extend(
            _parsed_property_to_property(
                parsed=parsed_prop,
                first_pass_type_annotator=first_pass_type_annotator
            )
            for parsed_prop in antecedent.properties
        )

    for parsed_prop in parsed.properties:
        properties.append(
            _parsed_property_to_property(
                parsed=parsed_prop,
                first_pass_type_annotator=first_pass_type_annotator))

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
        arguments = _parsed_arguments_to_arguments(
            parsed=parsed_entity_init.arguments,
            first_pass_type_annotator=first_pass_type_annotator
        )

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
        description=_parsed_description_to_description(parsed.description),
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

    first_pass_type_annotator = _FirstPassTypeAnnotator()

    # region First pass of translation; type annotations reference placeholder symbols

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
            symbol = _parsed_abstract_entity_to_interface(
                parsed=parsed_symbol,
                first_pass_type_annotator=first_pass_type_annotator)

        elif isinstance(parsed_symbol, parse.ConcreteEntity):
            symbol = _parsed_entity_to_class(
                parsed=parsed_symbol,
                ontology=ontology,
                in_lined_constructors=in_lined_constructors,
                first_pass_type_annotator=first_pass_type_annotator
            )

        else:
            assert_never(parsed_symbol)

        assert symbol is not None
        symbols.append(symbol)

    symbol_table = SymbolTable(symbols=symbols)

    # endregion

    # region Second pass to resolve the symbols in the atomic types

    for our_type_annotation in first_pass_type_annotator.to_be_resolved.values():
        assert isinstance(our_type_annotation.symbol, _PlaceholderSymbol), \
            "Expected only placeholder symbols to be assigned in the first pass"

        symbol = symbol_table.find(our_type_annotation.symbol.identifier)

        assert symbol is not None, \
            (
                f"The symbol {our_type_annotation.symbol.identifier} is not available "
                f"in the symbol table, but was assigned "
                f"in the first pass of the translation of the type annotations"
            )

        our_type_annotation.symbol = symbol

    # endregion

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

    return symbol_table, None
