"""Translate the parsed representation into the intermediate representation."""
import ast
import itertools
from typing import Sequence, List, Mapping, Optional, MutableMapping, Tuple, Union, \
    Iterator, Generator, TypeVar, Generic

import asttokens
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
from icontract import require, ensure

from aas_core_csharp_codegen import parse
from aas_core_csharp_codegen.common import Error, Identifier, assert_never, \
    IDENTIFIER_RE
from aas_core_csharp_codegen.intermediate import _hierarchy, construction
from aas_core_csharp_codegen.intermediate._types import (
    SymbolTable,
    Enumeration,
    EnumerationLiteral,
    TypeAnnotation,
    Argument,
    Default,
    DefaultConstant,
    Interface,
    Signature,
    Property,
    Invariant,
    Contracts,
    Contract,
    Snapshot,
    JsonSerialization,
    Method,
    Class,
    Constructor,
    Symbol, ListTypeAnnotation, SequenceTypeAnnotation, SetTypeAnnotation,
    MappingTypeAnnotation, MutableMappingTypeAnnotation, OptionalTypeAnnotation,
    OurAtomicTypeAnnotation, STR_TO_BUILTIN_ATOMIC_TYPE, BuiltinAtomicTypeAnnotation,
    Description, PropertyReferenceInDoc, SymbolReferenceInDoc,
    SubscriptedTypeAnnotation, DefaultEnumerationLiteral,
)

# noinspection PyUnusedLocal
from aas_core_csharp_codegen.specific_implementations import ImplementationKey


# noinspection PyUnusedLocal
def _symbol_reference_role(
        role, rawtext, text, lineno, inliner, options=None, content=None):
    """Create an element of the description as a reference to a symbol."""
    # See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
    if content is None:
        content = []

    if options is None:
        options = {}

    docutils.parsers.rst.roles.set_classes(options)

    # We need to create a placeholder as the symbol table might not be fully created
    # at the point when we translate the documentation.
    #
    # We have to resolve the placeholders in the second pass of the translation with
    # the actual references to the symbol table.
    symbol = _PlaceholderSymbol(identifier=text)

    # noinspection PyTypeChecker
    node = SymbolReferenceInDoc(
        symbol, rawtext, docutils.utils.unescape(text), refuri=text, **options
    )  # type: ignore
    return [node], []


# noinspection PyUnusedLocal
def _property_reference_role(
        role, rawtext, text, lineno, inliner, options=None, content=None):
    """Create an element of the description as a reference to a property."""
    # See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
    if content is None:
        content = []

    if options is None:
        options = {}

    docutils.parsers.rst.roles.set_classes(options)

    # We need to create a placeholder as the symbol table might not be fully created
    # at the point when we translate the documentation.
    #
    # We have to resolve the placeholders in the second pass of the translation with
    # the actual references to the symbol table.
    symbol = _PlaceholderSymbol(identifier=text)

    # We strip the tilde based on the convention as we ignore the appearance.
    # See: https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#cross-referencing-syntax
    property_name = text[1:] if text.startswith('~') else text

    node = PropertyReferenceInDoc(
        property_name, rawtext, docutils.utils.unescape(text), refuri=text, **options
    )
    return [node], []


# The global registration is unfortunate since it is unpredictable and might affect
# other modules, but it is the only way to register the roles.
#
# See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
docutils.parsers.rst.roles.register_local_role('class', _symbol_reference_role)
docutils.parsers.rst.roles.register_local_role('py:attr', _property_reference_role)


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
                description=(
                    _parsed_description_to_description(parsed_literal.description)
                    if parsed_literal.description is not None
                    else None),
                parsed=parsed_literal,
            )
            for parsed_literal in parsed.literals
        ],
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None),
        parsed=parsed,
    )


class _PlaceholderSymbol:
    """Reference a symbol which will be resolved once the table is built."""

    def __init__(self, identifier: str) -> None:
        """Initialize with the given values."""
        self.identifier = identifier


def _parsed_type_annotation_to_type_annotation(
        parsed: parse.TypeAnnotation
) -> TypeAnnotation:
    """
    Translate parsed type annotations to possibly unresolved type annotation.

    We need a two-pass translation to translate atomic type annotations to
    intermediate ones. Namely, we are translating the type annotations as we are
    building the symbol table. At that point, the atomic type annotations referring to
    meta-model entities can not be resolved (as the symbol table is not completely
    built yet). Therefore, we use placeholders which are eventually resolved in the
    second pass.
    """
    if isinstance(parsed, parse.AtomicTypeAnnotation):
        builtin_atomic_type = STR_TO_BUILTIN_ATOMIC_TYPE.get(
            parsed.identifier, None)

        if builtin_atomic_type is not None:
            return BuiltinAtomicTypeAnnotation(
                a_type=builtin_atomic_type, parsed=parsed)

        # noinspection PyTypeChecker
        return OurAtomicTypeAnnotation(
            symbol=_PlaceholderSymbol(identifier=parsed.identifier),  # type: ignore
            parsed=parsed)

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
                items=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed)

        elif parsed.identifier == 'Sequence':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Sequence type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return SequenceTypeAnnotation(
                items=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed)

        elif parsed.identifier == 'Set':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Set type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return SetTypeAnnotation(
                items=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed)

        elif parsed.identifier == 'Mapping':
            assert len(parsed.subscripts) == 2, (
                f"Expected exactly two subscripts for the Mapping type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return MappingTypeAnnotation(
                keys=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                values=_parsed_type_annotation_to_type_annotation(parsed.subscripts[1]),
                parsed=parsed)

        elif parsed.identifier == 'MutableMapping':
            assert len(parsed.subscripts) == 2, (
                f"Expected exactly two subscripts "
                f"for the MutableMapping type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return MutableMappingTypeAnnotation(
                keys=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                values=_parsed_type_annotation_to_type_annotation(parsed.subscripts[1]),
                parsed=parsed)

        elif parsed.identifier == 'Optional':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Optional type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return OptionalTypeAnnotation(
                value=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed)

        else:
            raise AssertionError(
                f"Unexpected subscripted type annotation identifier: "
                f"{parsed.identifier}. "
                f"This should have been handled or caught before!")

    elif isinstance(parsed, parse.SelfTypeAnnotation):
        raise AssertionError(
            f"Unexpected self type annotation in the intermediate layer: {parsed}")

    else:
        assert_never(parsed)
        raise AssertionError(parsed)


class _DefaultPlaceholder:
    """Hold a place for postponed translation of the default values.

    We can not translate the default argument values immediately while we are
    constructing the symbol table as they might reference, *e.g.*, enumeration
    literals which we still did not observe.

    Therefore we insert a placeholder and resolve the default values in the second
    translation pass.
    """

    def __init__(self, parsed: parse.Default) -> None:
        """Initialize with the given values."""
        self.parsed = parsed


def _parsed_arguments_to_arguments(
        parsed: Sequence[parse.Argument]
) -> List[Argument]:
    """Translate the arguments of a method in meta-model to the intermediate ones."""
    return [
        Argument(
            name=parsed_arg.name,
            type_annotation=_parsed_type_annotation_to_type_annotation(
                parsed_arg.type_annotation),
            default=_DefaultPlaceholder(parsed=parsed_arg.default)  # type: ignore
            if parsed_arg.default is not None
            else None,
            parsed=parsed_arg,
        )
        for parsed_arg in parsed
        if not isinstance(parsed_arg.type_annotation, parse.SelfTypeAnnotation)
    ]


def _parsed_abstract_entity_to_interface(
        parsed: parse.AbstractEntity
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
                    parsed=parsed_method.arguments),
                returns=(
                    None
                    if parsed_method.returns is None
                    else _parsed_type_annotation_to_type_annotation(
                        parsed_method.returns)
                ),
                description=(
                    _parsed_description_to_description(parsed_method.description)
                    if parsed_method.description is not None
                    else None),
                parsed=parsed_method,
            )
            for parsed_method in parsed.methods
            if parsed_method.name != "__init__"
        ],
        properties=[
            _parsed_property_to_property(parsed=parsed_prop)
            for parsed_prop in parsed.properties
        ],
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None),
        parsed=parsed,
    )


def _parsed_property_to_property(parsed: parse.Property) -> Property:
    """Translate a parsed property of a class to an intermediate one."""
    return Property(
        name=parsed.name,
        type_annotation=_parsed_type_annotation_to_type_annotation(
            parsed.type_annotation),
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None),
        is_readonly=parsed.is_readonly,
        parsed=parsed,
    )


def _parsed_contracts_to_contracts(
        parsed: parse.Contracts
) -> Contracts:
    """Translate the parsed contracts into intermediate ones."""
    return Contracts(
        preconditions=[
            Contract(
                args=parsed_pre.args,
                description=parsed_pre.description,
                body=parsed_pre.condition.body,
                parsed=parsed_pre,
            )
            for parsed_pre in parsed.preconditions
        ],
        snapshots=[
            Snapshot(
                args=parsed_snap.args,
                body=parsed_snap.capture.body,
                name=parsed_snap.name,
                parsed=parsed_snap,
            )
            for parsed_snap in parsed.snapshots
        ],
        postconditions=[
            Contract(
                args=parsed_post.args,
                description=parsed_post.description,
                body=parsed_post.condition.body,
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
        original_entity: parse.Entity
) -> Method:
    """Translate the parsed method into an intermediate representation."""
    implementation_key = None  # type: Optional[ImplementationKey]
    if parsed.is_implementation_specific:
        implementation_key = ImplementationKey(f"{original_entity.name}/{parsed.name}")

    return Method(
        name=parsed.name,
        implementation_key=implementation_key,
        arguments=_parsed_arguments_to_arguments(parsed=parsed.arguments),
        returns=(
            None
            if parsed.returns is None
            else _parsed_type_annotation_to_type_annotation(parsed.returns)
        ),
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None),
        contracts=_parsed_contracts_to_contracts(parsed.contracts),
        body=parsed.body,
        parsed=parsed,
    )


def _in_line_constructors(
        parsed_symbol_table: parse.SymbolTable,
        ontology: _hierarchy.Ontology,
        constructor_table: construction.ConstructorTable,
) -> Mapping[parse.Entity, Sequence[construction.AssignArgument]]:
    """In-line recursively all the constructor bodies."""
    result = (
        dict()
    )  # type: MutableMapping[parse.Entity, List[construction.AssignArgument]]

    for entity in ontology.entities:
        # We explicitly check at the stage of
        # :py:mod:`aas_core_csharp_codegen.intermediate.constructor` that all the calls
        # are calls to constructors of a super class or property assignments.

        constructor_body = constructor_table.must_find(entity)
        in_lined = []  # type: List[construction.AssignArgument]
        for statement in constructor_body:
            if isinstance(statement, construction.CallSuperConstructor):
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
                in_lined.append(statement)

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


T = TypeVar('T')


class _SettingWithSource(Generic[T]):
    """
    Represent a setting from an inheritance chain.

    For example, a setting for JSON serialization.
    """

    def __init__(self, value: T, source: parse.Entity):
        """Initialize with the given values."""
        self.value = value
        self.source = source


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _resolve_inheritance_chain_of_a_setting(
        chain: Sequence[_SettingWithSource[T]],
        default: T
) -> Tuple[Optional[T], Optional[str]]:
    """
    Resolve the inheritance chain for a setting.

    Return either the resolved value, or an error.
    """
    # TODO: consider removing this function as well once we implemented O(N) json serialization
    #  resolution.

    if len(chain) == 0:
        return default, None

    last_setting = None  # type: Optional[_SettingWithSource]

    for setting in chain:
        if last_setting is not None and setting.value != last_setting.value:
            return None, (
                f"The setting for the entity {setting.source.name} "
                f"says {setting.value!r}, "
                f"but the entity {last_setting.source.name} "
                f"says {last_setting.value!r}")

        last_setting = setting

    return last_setting.value, None


# fmt: off
@ensure(
    lambda parsed_symbol_table, result:
    all(
        symbol.name in result
        for symbol in parsed_symbol_table
        if not isinstance(symbol, parse.Enumeration)
    ),
    "Resolution of JSON settings performed for all non-enumeration symbols"
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _resolve_json_serializations(
        parsed_symbol_table: parse.SymbolTable,
        ontology: _hierarchy.Ontology
) -> Tuple[
    Optional[MutableMapping[Identifier, JsonSerialization]],
    Optional[Error]]:
    """Resolve how JSON serialization settings stack through the ontology."""
    settings_map = dict(
    )  # type: MutableMapping[Identifier, Optional[_SettingWithSource]]

    errors = []  # type: List[Error]

    for entity in ontology.entities:
        assert entity.name not in settings_map, (
                f"Expected the ontology to be a correctly linearized DAG, "
                f"but the entity {entity.name!r} has been already visited before")

        settings = []  # type: List[_SettingWithSource]

        if (
                entity.json_serialization is not None
                and entity.json_serialization.with_model_type
        ):
            settings.append(
                _SettingWithSource(
                    value=entity.json_serialization.with_model_type,
                    source=entity))

        for inheritance in entity.inheritances:
            assert inheritance in settings_map, (
                f"Expected the ontology to be a correctly linearized DAG, "
                f"but the inheritance {inheritance!r} of the entity {entity.name!r} "
                f"has not been visited before."
            )

            setting = settings_map[inheritance]
            if setting is None:
                continue

            settings.append(setting)

        if len(settings) > 1:
            # Verify that the setting for the entity as well as all the inherited
            # settings are consistent.
            for setting in settings[1:]:
                if setting.value != settings[0].value:
                    return None, Error(
                        entity.node,
                        f"The setting ``with_model_type`` "
                        f"for JSON serialization "
                        f"between the entity {setting.source} "
                        f"and {settings[0].source} is "
                        f"inconsistent")

        settings_map[entity.name] = (
            None
            if len(settings) == 0
            else settings[0])

    # TODO: resolve the settings to the actual values 🠒 where it's None, it must be False




@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _stack_json_serializations(
        entity: parse.Entity,
        antecedents: Sequence[parse.Entity]
) -> Tuple[Optional[JsonSerialization], Optional[Error]]:
    """Effectuate inheritance of json serialization settings through antecedents."""
    # TODO: remove the following function once we implemented O(N) resolution

    # TODO: test this function
    # TODO: test also the failure cases

    # NOTE (mristin, 2021-10-27):
    # We decided to encapsulate the chain resolution to a separate function.
    # The original implementation, where the chain has been locally resolved, was
    # quite unreadable and can not scale for XML and other settings.

    chain = list(antecedents) + [entity]

    with_model_type_chain = [
        _SettingWithSource(
            value=an_entity_in_chain.json_serialization.with_model_type,
            source=an_entity_in_chain)
        for an_entity_in_chain in chain
        if (
                an_entity_in_chain.json_serialization is not None
                and an_entity_in_chain.json_serialization.with_model_type is not None
        )
    ]  # type: List[_SettingWithSource[bool]]

    with_model_type, error_message = _resolve_inheritance_chain_of_a_setting(
        chain=with_model_type_chain, default=False)

    if error_message:
        return None, Error(
            entity.node,
            f"Failed to resolve the chain for setting ``with_model_type`` "
            f"for JSON serialization: {error_message}")

    return JsonSerialization(with_model_type=with_model_type), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _parsed_entity_to_class(
        parsed: parse.ConcreteEntity,
        ontology: _hierarchy.Ontology,
        in_lined_constructors: Mapping[
            parse.Entity, Sequence[construction.AssignArgument]]
) -> Tuple[Optional[Class], Optional[Error]]:
    """Translate a concrete entity to an intermediate class."""
    antecedents = ontology.list_antecedents(entity=parsed)

    # region Stack properties from the antecedents

    properties = []  # type: List[Property]

    # We explicitly check that there are no property overloads at the parse stage so
    # we do not perform the same check here for the second time.

    for antecedent in antecedents:
        properties.extend(
            _parsed_property_to_property(parsed=parsed_prop)
            for parsed_prop in antecedent.properties
        )

    for parsed_prop in parsed.properties:
        properties.append(
            _parsed_property_to_property(parsed=parsed_prop))

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
    init_is_implementation_specific = False

    parsed_entity_init = parsed.method_map.get(Identifier("__init__"), None)
    if parsed_entity_init is not None:
        arguments = _parsed_arguments_to_arguments(parsed=parsed_entity_init.arguments)

        init_is_implementation_specific = parsed_entity_init.is_implementation_specific

        contracts = _stack_contracts(
            contracts, _parsed_contracts_to_contracts(parsed_entity_init.contracts)
        )

    init_implementation_key = None  # type: Optional[ImplementationKey]
    if init_is_implementation_specific:
        init_implementation_key = ImplementationKey(f"{parsed.name}/__init__")

    ctor = Constructor(
        arguments=arguments,
        contracts=contracts,
        implementation_key=init_implementation_key,
        statements=in_lined_constructors[parsed],
    )

    # endregion

    # region Stack methods from the antecedents

    methods = []  # type: List[Method]

    # We explicitly check that there are no method overloads at the parse stage
    # so we do not perform this check for the second time here.

    for antecedent in antecedents:
        methods.extend(
            _parsed_method_to_method(parsed=parsed_method, original_entity=antecedent)
            for parsed_method in antecedent.methods
            if parsed_method.name != "__init__"
        )

    for parsed_method in parsed.methods:
        if parsed_method.name == "__init__":
            # Constructors are in-lined and handled in a different way through
            # :py:class:`Constructors`.
            continue

        methods.append(
            _parsed_method_to_method(parsed=parsed_method, original_entity=parsed))

    # endregion

    # region Stack the invariants from the antecedents

    invariants = []  # type: List[Invariant]

    for antecedent in antecedents:
        for parsed_invariant in antecedent.invariants:
            invariants.append(
                Invariant(
                    description=parsed_invariant.description,
                    parsed=parsed_invariant))

    errors = []  # type: List[Error]

    for parsed_invariant in parsed.invariants:
        invariants.append(
            Invariant(
                description=parsed_invariant.description,
                parsed=parsed_invariant))

    # endregion

    # region Stack settings for JSON serialization

    json_serialization, error = _stack_json_serializations(
        entity=parsed, antecedents=antecedents)

    if error is not None:
        errors.append(error)

    # endregion

    if len(errors) > 0:
        return None, Error(
            node=parsed.node,
            message=f"Failed to translate the class {parsed.name} "
                    f"to the intermediate representation",
            underlying=errors)

    assert json_serialization is not None

    return Class(
        name=parsed.name,
        interfaces=parsed.inheritances,
        implementation_key=(
            ImplementationKey(parsed.name)
            if parsed.is_implementation_specific
            else None),
        properties=properties,
        methods=methods,
        constructor=ctor,
        invariants=invariants,
        json_serialization=json_serialization,
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None),
        parsed=parsed,
    ), None


def _over_our_atomic_type_annotations(
        something: Union[Class, Interface, TypeAnnotation]
) -> Iterator[OurAtomicTypeAnnotation]:
    """Iterate over all the atomic type annotations in the ``something``."""
    if isinstance(something, BuiltinAtomicTypeAnnotation):
        pass
    elif isinstance(something, OurAtomicTypeAnnotation):
        yield something
    elif isinstance(something, SubscriptedTypeAnnotation):
        if isinstance(something, ListTypeAnnotation):
            yield from _over_our_atomic_type_annotations(something.items)
        elif isinstance(something, SequenceTypeAnnotation):
            yield from _over_our_atomic_type_annotations(something.items)
        elif isinstance(something, SetTypeAnnotation):
            yield from _over_our_atomic_type_annotations(something.items)
        elif isinstance(something, MappingTypeAnnotation):
            yield from _over_our_atomic_type_annotations(something.keys)
            yield from _over_our_atomic_type_annotations(something.values)
        elif isinstance(something, MutableMappingTypeAnnotation):
            yield from _over_our_atomic_type_annotations(something.keys)
            yield from _over_our_atomic_type_annotations(something.values)
        elif isinstance(something, OptionalTypeAnnotation):
            yield from _over_our_atomic_type_annotations(something.value)
        else:
            assert_never(something)

    elif isinstance(something, Class):
        for prop in something.properties:
            yield from _over_our_atomic_type_annotations(prop.type_annotation)

        for method in something.methods:
            for argument in method.arguments:
                yield from _over_our_atomic_type_annotations(
                    argument.type_annotation)

            if method.returns is not None:
                yield from _over_our_atomic_type_annotations(method.returns)

        for argument in something.constructor.arguments:
            yield from _over_our_atomic_type_annotations(argument.type_annotation)

    elif isinstance(something, Interface):
        for prop in something.properties:
            yield from _over_our_atomic_type_annotations(prop.type_annotation)

        for signature in something.signatures:
            for argument in signature.arguments:
                yield from _over_our_atomic_type_annotations(
                    argument.type_annotation)

            if signature.returns is not None:
                yield from _over_our_atomic_type_annotations(signature.returns)


def _over_descriptions(
        something: Union[Class, Interface, Enumeration]
) -> Iterator[Description]:
    """Iterate over all the descriptions from the entity ``something``."""
    if isinstance(something, Class):
        if something.description is not None:
            yield something.description

        for prop in something.properties:
            if prop.description is not None:
                yield prop.description

        for method in something.methods:
            if method.description is not None:
                yield method.description

    elif isinstance(something, Interface):
        if something.description is not None:
            yield something.description

        for prop in something.properties:
            if prop.description is not None:
                yield prop.description

        for signature in something.signatures:
            if signature.description is not None:
                yield signature.description

    elif isinstance(something, Enumeration):
        if something.description is not None:
            yield something.description

        for literal in something.literals:
            if literal.description is not None:
                yield literal.description

    elif isinstance(something, Description):
        for node in something.document.traverse(condition=SymbolReferenceInDoc):
            yield something, node
    else:
        assert_never(something)


def _over_symbol_reference_in_doc(
        something: Union[Class, Interface, Enumeration, Description]
) -> Iterator[Tuple[Description, SymbolReferenceInDoc]]:
    """Iterate over all the descriptions and their symbol references."""
    if isinstance(something, Class):
        if something.description is not None:
            yield from _over_symbol_reference_in_doc(something.description)

        for prop in something.properties:
            if prop.description is not None:
                yield from _over_symbol_reference_in_doc(prop.description)

        for method in something.methods:
            if method.description is not None:
                yield from _over_symbol_reference_in_doc(method.description)

    elif isinstance(something, Interface):
        if something.description is not None:
            yield from _over_symbol_reference_in_doc(something.description)

        for prop in something.properties:
            if prop.description is not None:
                yield from _over_symbol_reference_in_doc(prop.description)

        for signature in something.signatures:
            if signature.description is not None:
                yield from _over_symbol_reference_in_doc(signature.description)

    elif isinstance(something, Enumeration):
        if something.description is not None:
            yield from _over_symbol_reference_in_doc(something.description)

        for literal in something.literals:
            if literal.description is not None:
                yield from _over_symbol_reference_in_doc(literal.description)

    elif isinstance(something, Description):
        for node in something.document.traverse(condition=SymbolReferenceInDoc):
            yield something, node
    else:
        assert_never(something)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _fill_in_default_placeholder(
        default: _DefaultPlaceholder,
        symbol_table: SymbolTable
) -> Tuple[Optional[Default], Optional[Error]]:
    """Resolve the default values to references using the constructed symbol table."""
    # If we do not preemptively return, signal that we do not know how to handle
    # the default

    if isinstance(default.parsed.node, ast.Constant):
        if (
                isinstance(default.parsed.node.value, (bool, int, float, str))
                or default.parsed.node.value is None
        ):
            return DefaultConstant(
                value=default.parsed.node.value,
                parsed=default.parsed), None

    if (
            isinstance(default.parsed.node, ast.Attribute)
            and isinstance(default.parsed.node.ctx, ast.Load)
            and isinstance(default.parsed.node.value, ast.Name)
            and isinstance(default.parsed.node.value.ctx, ast.Load)
    ):
        symbol_name = Identifier(default.parsed.node.value.id)
        attr_name = Identifier(default.parsed.node.attr)

        symbol = symbol_table.find(name=symbol_name)
        if isinstance(symbol, Enumeration):
            literal = symbol.literals_by_name.get(attr_name, None)
            if literal is not None:
                return DefaultEnumerationLiteral(
                    enumeration=symbol,
                    literal=literal,
                    parsed=default.parsed), None

    return None, Error(
        default.parsed.node,
        f"The translation of the default value to the intermediate layer "
        f"has not been implemented: {ast.dump(default.parsed.node)}")


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def translate(
        parsed_symbol_table: parse.SymbolTable,
        atok: asttokens.ASTTokens,
) -> Tuple[Optional[SymbolTable], Optional[Error]]:
    """Translate the parsed symbols into intermediate symbols."""
    underlying_errors = []  # type: List[Error]

    def bundle_underlying_errors() -> Error:
        """Bundle underlying errors to the main error."""
        return Error(
            atok.tree,
            "Failed to translate the parsed symbol table "
            "to an intermediate symbol table",
            underlying=underlying_errors)

    # region Infer hierarchy as ontology

    ontology, errors = _hierarchy.map_symbol_table_to_ontology(
        parsed_symbol_table=parsed_symbol_table
    )
    if errors is not None:
        underlying_errors = errors
        return None, bundle_underlying_errors()

    assert ontology is not None

    # endregion

    # region Understand constructor stacks

    constructor_table, error = construction.understand_all(
        parsed_symbol_table=parsed_symbol_table, atok=atok)

    if error is not None:
        underlying_errors = [error]
        return None, bundle_underlying_errors()

    assert constructor_table is not None

    in_lined_constructors = _in_line_constructors(
        parsed_symbol_table=parsed_symbol_table,
        ontology=ontology,
        constructor_table=constructor_table,
    )

    # endregion

    # region First pass of translation; type annotations reference placeholder symbols

    symbols = []  # type: List[Symbol]
    for parsed_symbol in parsed_symbol_table.symbols:
        symbol = None  # type: Optional[Symbol]

        if isinstance(parsed_symbol, parse.Enumeration):
            symbol = _parsed_enumeration_to_enumeration(parsed=parsed_symbol)

        elif isinstance(parsed_symbol, parse.AbstractEntity):
            symbol = _parsed_abstract_entity_to_interface(parsed=parsed_symbol)

        elif isinstance(parsed_symbol, parse.ConcreteEntity):
            symbol, error = _parsed_entity_to_class(
                parsed=parsed_symbol,
                ontology=ontology,
                in_lined_constructors=in_lined_constructors)

            if error is not None:
                underlying_errors.append(error)
                continue

        else:
            assert_never(parsed_symbol)

        assert symbol is not None
        symbols.append(symbol)

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    symbol_table = SymbolTable(symbols=symbols)

    # endregion

    # region Second pass to resolve the symbols in the atomic types

    for symbol in symbols:
        if isinstance(symbol, Enumeration):
            continue

        for our_type_annotation in _over_our_atomic_type_annotations(symbol):
            assert isinstance(our_type_annotation.symbol, _PlaceholderSymbol), \
                "Expected only placeholder symbols to be assigned in the first pass"

            if not IDENTIFIER_RE.match(our_type_annotation.symbol.identifier):
                underlying_errors.append(
                    Error(
                        our_type_annotation.parsed.node,
                        f"The symbol is invalid: "
                        f"{our_type_annotation.symbol.identifier!r}"))
                continue

            identifier = Identifier(our_type_annotation.symbol.identifier)
            symbol = symbol_table.find(identifier)
            if symbol is None:
                underlying_errors.append(
                    Error(
                        our_type_annotation.parsed.node,
                        f"The symbol with identifier {identifier!r} is not available "
                        f"in the symbol table."))
                continue

            our_type_annotation.symbol = symbol

    # endregion

    # region Second pass to resolve the symbols in the descriptions

    for symbol in symbols:
        for description in _over_descriptions(symbol):
            for symbol_ref_in_doc in description.document.traverse(
                    condition=SymbolReferenceInDoc):
                assert isinstance(
                    symbol_ref_in_doc.symbol, _PlaceholderSymbol), (
                    f"Expected all symbol references in the descriptions "
                    f"to be placeholder since only the first pass has been executed, "
                    f"but we got: {symbol_ref_in_doc.symbol}")

                raw_identifier = symbol_ref_in_doc.symbol.identifier
                if not raw_identifier.startswith("."):
                    underlying_errors.append(
                        Error(
                            description.node,
                            f"The identifier of the symbol reference "
                            f"is invalid: {raw_identifier}; "
                            f"expected an identifier starting with a dot"))
                    continue

                raw_identifier_no_dot = raw_identifier[1:]

                if not IDENTIFIER_RE.match(raw_identifier_no_dot):
                    underlying_errors.append(
                        Error(
                            description.node,
                            f"The identifier of the symbol reference "
                            f"is invalid: {raw_identifier_no_dot}"))
                    continue

                # Strip the dot
                identifier = Identifier(raw_identifier_no_dot)

                symbol = symbol_table.find(name=identifier)
                if symbol is None:
                    underlying_errors.append(
                        Error(
                            description.node,
                            f"The identifier of the symbol reference "
                            f"could not be found in the symbol table: {identifier}"))
                    continue

                symbol_ref_in_doc.symbol = symbol

    # endregion

    # region Second pass to resolve the default argument values

    for symbol in symbols:
        if isinstance(symbol, Enumeration):
            continue

        elif isinstance(symbol, (Interface, Class)):
            args_generator = None  # type: Optional[Generator[Argument]]

            if isinstance(symbol, Interface):
                args_generator = (
                    arg
                    for signature in symbol.signatures
                    for arg in signature.arguments
                )
            elif isinstance(symbol, Class):
                # noinspection PyTypeChecker
                args_generator = itertools.chain(
                    (
                        arg
                        for method in symbol.methods
                        for arg in method.arguments
                    ),
                    iter(symbol.constructor.arguments))
            else:
                assert_never(symbol)

            assert args_generator is not None

            for arg in args_generator:
                if arg.default is not None:
                    assert isinstance(arg.default, _DefaultPlaceholder), (
                        f"Expected the argument default value to be a placeholder "
                        f"since we resolve it only in the second pass, "
                        f"but got: {arg.default}")

                    filled_default, error = _fill_in_default_placeholder(
                        default=arg.default,
                        symbol_table=symbol_table)

                    if error:
                        underlying_errors.append(error)
                    else:
                        arg.default = filled_default
        else:
            assert_never(symbol)

    # endregion

    # region Verify that all property references in the descriptions are valid

    # TODO: test this
    for symbol in symbols:
        for description in _over_descriptions(symbol):
            for prop_ref_in_doc in description.document.traverse(
                    condition=PropertyReferenceInDoc):
                if "." in prop_ref_in_doc.property_name:
                    underlying_errors.append(
                        Error(
                            description.node,
                            f"Unexpected complex reference to a property: "
                            f"{prop_ref_in_doc.property_name}"))
                    continue

                if not IDENTIFIER_RE.match(prop_ref_in_doc.property_name):
                    underlying_errors.append(
                        Error(
                            description.node,
                            f"Invalid identifier of a property: "
                            f"{prop_ref_in_doc.property_name}"))
                    continue

    # endregion

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    return symbol_table, None
