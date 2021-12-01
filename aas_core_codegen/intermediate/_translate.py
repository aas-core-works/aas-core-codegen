"""Translate the parsed representation into the intermediate representation."""
import ast
import itertools
import re
from typing import Sequence, List, Mapping, Optional, MutableMapping, Tuple, Union, \
    Iterator, Generator, TypeVar, Generic, cast

import asttokens
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
from icontract import require, ensure

from aas_core_codegen import parse
from aas_core_codegen.common import Error, Identifier, assert_never, \
    IDENTIFIER_RE
from aas_core_codegen.intermediate import _hierarchy, construction
from aas_core_codegen.intermediate._types import (
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
    Serialization,
    Method,
    Class,
    Constructor,
    Symbol, ListTypeAnnotation,
    OptionalTypeAnnotation,
    OurAtomicTypeAnnotation, STR_TO_BUILTIN_ATOMIC_TYPE, BuiltinAtomicTypeAnnotation,
    Description, AttributeReferenceInDoc, SymbolReferenceInDoc,
    SubscriptedTypeAnnotation, DefaultEnumerationLiteral,
    EnumerationLiteralReferenceInDoc, PropertyReferenceInDoc, MetaModel,
    RefTypeAnnotation, collect_ids_of_interfaces_in_properties,
    map_interface_implementers,
)


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


_ATTRIBUTE_REFERENCE_RE = re.compile(
    r'[a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)?')


class _PlaceholderAttributeReference:
    """
    Represent a placeholder object masking a proper attribute reference.

    The attribute, in this context, refers either to a property of a class or a literal
    of an enumeration. This placeholder needs to be used till we create the symbol
    table in full, so that we can properly de-reference the symbols.
    """

    @require(lambda path: _ATTRIBUTE_REFERENCE_RE.fullmatch(path))
    def __init__(self, path: str) -> None:
        """Initialize with the given values."""
        self.path = path


# noinspection PyUnusedLocal
def _attribute_reference_role(
        role, rawtext, text, lineno, inliner, options=None, content=None):
    """Create a reference in the documentation to a property or a literal."""
    # See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
    if content is None:
        content = []

    if options is None:
        options = {}

    docutils.parsers.rst.roles.set_classes(options)

    # We strip the tilde based on the convention as we ignore the appearance.
    # See: https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#cross-referencing-syntax
    path = text[1:] if text.startswith('~') else text

    # We need to create a placeholder as the symbol table might not be fully created
    # at the point when we translate the documentation.
    #
    # We have to resolve the placeholders in the second pass of the translation with
    # the actual references to the symbol table.

    placeholder = _PlaceholderAttributeReference(path=path)

    # noinspection PyTypeChecker
    node = AttributeReferenceInDoc(
        placeholder, rawtext, docutils.utils.unescape(text), refuri=text, **options
    )
    return [node], []


# The global registration is unfortunate since it is unpredictable and might affect
# other modules, but it is the only way to register the roles.
#
# See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
docutils.parsers.rst.roles.register_local_role('class', _symbol_reference_role)
docutils.parsers.rst.roles.register_local_role('attr', _attribute_reference_role)


def _parsed_description_to_description(parsed: parse.Description) -> Description:
    """Translate the parsed description to an intermediate form."""
    # This function makes a simple copy at the moment, which might seem pointless.
    #
    # However, we want to explicitly delineate layers (the parse and the intermediate
    # layer, respectively). This simple copying thus helps the understanding
    # of the general system and allows the reader to ignore, to a certain degree, the
    # parse layer when examining the output of the intermediate layer.
    return Description(document=parsed.document, node=parsed.node)


class _PlaceholderSymbol:
    """Reference a symbol which will be resolved once the table is built."""

    def __init__(self, identifier: str) -> None:
        """Initialize with the given values."""
        self.identifier = identifier


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
        # Postpone the resolution to the second pass once the symbol table has been
        # completely built
        is_superset_of=cast(List[Enumeration], [
            _PlaceholderSymbol(identifier=identifier)
            for identifier in parsed.is_superset_of
        ]),
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None),
        parsed=parsed,
    )


def _parsed_type_annotation_to_type_annotation(
        parsed: parse.TypeAnnotation
) -> TypeAnnotation:
    """
    Translate parsed type annotations to possibly unresolved type annotation.

    We need a two-pass translation to translate atomic type annotations to
    intermediate ones. Namely, we are translating the type annotations as we are
    building the symbol table. At that point, the atomic type annotations referring to
    meta-model classes can not be resolved (as the symbol table is not completely
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
        if parsed.identifier == 'List':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the List type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return ListTypeAnnotation(
                items=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed)

        elif parsed.identifier == 'Optional':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Optional type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return OptionalTypeAnnotation(
                value=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed)

        elif parsed.identifier == 'Ref':
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Ref type annotation, "
                f"but got: {parsed}; this should have been caught before!")

            return RefTypeAnnotation(
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


def _parsed_abstract_class_to_interface(
        parsed: parse.AbstractClass,
        serializations: Mapping[parse.Class, Serialization]
) -> Interface:
    """Translate an abstract class of a meta-model to an intermediate interface."""
    # noinspection PyTypeChecker
    return Interface(
        name=parsed.name,
        inheritances=[
            _PlaceholderSymbol(inheritance)
            for inheritance in parsed.inheritances
        ],
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
            _parsed_property_to_property(parsed=parsed_prop, cls=parsed)
            for parsed_prop in parsed.properties
        ],
        serialization=serializations[parsed],
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None),
        parsed=parsed,
    )


def _parsed_property_to_property(
        parsed: parse.Property,
        cls: parse.Class
) -> Property:
    """Translate a parsed property of a class to an intermediate one."""
    # noinspection PyTypeChecker
    return Property(
        name=parsed.name,
        type_annotation=_parsed_type_annotation_to_type_annotation(
            parsed.type_annotation),
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None),
        implemented_for=_PlaceholderSymbol(cls.name),
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
        parsed: parse.Method
) -> Method:
    """Translate the parsed method into an intermediate representation."""
    return Method(
        name=parsed.name,
        is_implementation_specific=parsed.is_implementation_specific,
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
) -> Mapping[parse.Class, Sequence[construction.AssignArgument]]:
    """In-line recursively all the constructor bodies."""
    result = (
        dict()
    )  # type: MutableMapping[parse.Class, List[construction.AssignArgument]]

    for cls in ontology.classes:
        # We explicitly check at the stage of
        # :py:mod:`aas_core_codegen.intermediate.constructor` that all the calls
        # are calls to constructors of a super class or property assignments.

        constructor_body = constructor_table.must_find(cls)
        in_lined = []  # type: List[construction.AssignArgument]
        for statement in constructor_body:
            if isinstance(statement, construction.CallSuperConstructor):
                antecedent = parsed_symbol_table.must_find_class(statement.super_name)

                in_lined_of_antecedent = result.get(antecedent, None)

                assert in_lined_of_antecedent is not None, (
                    f"Expected all the constructors of the antecedents "
                    f"of the class {cls.name} to have been in-lined before "
                    f"due to the topological order of classes in the ontology, "
                    f"but the antecedent {antecedent.name} has not had its "
                    f"constructor in-lined yet"
                )

                in_lined.extend(in_lined_of_antecedent)
            else:
                in_lined.append(statement)

        assert cls not in result, (
            f"Expected the class {cls} not to be inserted into the registry of "
            f"in-lined constructors since its in-lined constructor "
            f"has just been computed."
        )

        result[cls] = in_lined

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

    def __init__(self, value: T, source: parse.Class):
        """Initialize with the given values."""
        self.value = value
        self.source = source


# fmt: off
@ensure(
    lambda parsed_symbol_table, result:
    not (result[0] is not None)
    or all(
        symbol in result[0]
        for symbol in parsed_symbol_table.symbols
        if not isinstance(symbol, parse.Enumeration)
    ),
    "Resolution of serialization settings performed for all non-enumeration symbols"
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _resolve_serializations(
        ontology: _hierarchy.Ontology,
        parsed_symbol_table: parse.SymbolTable
) -> Tuple[Optional[MutableMapping[parse.Class, Serialization]], Optional[Error]]:
    """Resolve how general serialization settings stack through the ontology."""
    # NOTE (mristin, 2021-11-03):
    # We do not abstract away different serialization settings at this point
    # as there is only a single one, ``with_model_type``. In the future, if there are
    # more settings, this function needs to be split into multiple ones (one function
    # for a setting each), or maybe we can even think of a more general approach to
    # inheritance of serialization settings.

    # region ``with_model_type``

    with_model_type_map = dict(
    )  # type: MutableMapping[Identifier, Optional[_SettingWithSource]]

    for cls in ontology.classes:
        assert cls.name not in with_model_type_map, (
            f"Expected the ontology to be a correctly linearized DAG, "
            f"but the class {cls.name!r} has been already visited before")

        settings = []  # type: List[_SettingWithSource[bool]]

        if (
                cls.serialization is not None
                and cls.serialization.with_model_type
        ):
            settings.append(
                _SettingWithSource(
                    value=cls.serialization.with_model_type,
                    source=cls))

        for inheritance in cls.inheritances:
            assert inheritance in with_model_type_map, (
                f"Expected the ontology to be a correctly linearized DAG, "
                f"but the inheritance {inheritance!r} of the class {cls.name!r} "
                f"has not been visited before."
            )

            setting = with_model_type_map[inheritance]
            if setting is None:
                continue

            settings.append(setting)

        if len(settings) > 1:
            # Verify that the setting for the class as well as all the inherited
            # settings are consistent.
            for setting in settings[1:]:
                if setting.value != settings[0].value:
                    # NOTE (mristin, 2021-11-03):
                    # We have to return immediately at the first error and can not
                    # continue to interpret the remainder of the hierarchy since
                    # a single inconsistency impedes us to make synchronization
                    # points for a viable error recovery.

                    return None, Error(
                        cls.node,
                        f"The serialization setting ``with_model_type`` "
                        f"between the class {setting.source} "
                        f"and {settings[0].source} is "
                        f"inconsistent")

        with_model_type_map[cls.name] = (
            None
            if len(settings) == 0
            else settings[0])

    # endregion

    mapping = dict(
    )  # type: MutableMapping[parse.Class, Serialization]

    for identifier, setting in with_model_type_map.items():
        cls = parsed_symbol_table.must_find_class(name=identifier)
        if setting is None:
            # Neither the current class nor its antecedents specified the setting
            # so we assume the default value.
            mapping[cls] = Serialization(with_model_type=False)
        else:
            mapping[cls] = Serialization(with_model_type=setting.value)

    return mapping, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _parsed_class_to_class(
        parsed: parse.ConcreteClass,
        ontology: _hierarchy.Ontology,
        serializations: Mapping[parse.Class, Serialization],
        in_lined_constructors: Mapping[
            parse.Class, Sequence[construction.AssignArgument]]
) -> Tuple[Optional[Class], Optional[Error]]:
    """Translate a concrete parsed class to an intermediate class."""
    antecedents = ontology.list_antecedents(cls=parsed)

    # region Stack properties from the antecedents

    properties = []  # type: List[Property]

    # We explicitly check that there are no property overloads at the parse stage so
    # we do not perform the same check here for the second time.

    for antecedent in antecedents:
        properties.extend(
            _parsed_property_to_property(parsed=parsed_prop, cls=antecedent)
            for parsed_prop in antecedent.properties
        )

    for parsed_prop in parsed.properties:
        properties.append(
            _parsed_property_to_property(parsed=parsed_prop, cls=parsed))

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

    parsed_class_init = parsed.method_map.get(Identifier("__init__"), None)
    if parsed_class_init is not None:
        arguments = _parsed_arguments_to_arguments(parsed=parsed_class_init.arguments)

        init_is_implementation_specific = parsed_class_init.is_implementation_specific

        contracts = _stack_contracts(
            contracts, _parsed_contracts_to_contracts(parsed_class_init.contracts)
        )

    ctor = Constructor(
        arguments=arguments,
        contracts=contracts,
        is_implementation_specific=init_is_implementation_specific,
        statements=in_lined_constructors[parsed],
    )

    # endregion

    # region Stack methods from the antecedents

    methods = []  # type: List[Method]

    # We explicitly check that there are no method overloads at the parse stage
    # so we do not perform this check for the second time here.

    for antecedent in antecedents:
        methods.extend(
            _parsed_method_to_method(parsed=parsed_method)
            for parsed_method in antecedent.methods
            if parsed_method.name != "__init__"
        )

    for parsed_method in parsed.methods:
        if parsed_method.name == "__init__":
            # Constructors are in-lined and handled in a different way through
            # :py:class:`Constructors`.
            continue

        methods.append(
            _parsed_method_to_method(parsed=parsed_method))

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

    if len(errors) > 0:
        return None, Error(
            node=parsed.node,
            message=f"Failed to translate the class {parsed.name} "
                    f"to the intermediate representation",
            underlying=errors)

    # noinspection PyTypeChecker
    return Class(
        name=parsed.name,
        interfaces=[
            _PlaceholderSymbol(inheritance)
            for inheritance in parsed.inheritances
        ],
        is_implementation_specific=parsed.is_implementation_specific,
        properties=properties,
        methods=methods,
        constructor=ctor,
        invariants=invariants,
        serialization=serializations[parsed],
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
        elif isinstance(something, OptionalTypeAnnotation):
            yield from _over_our_atomic_type_annotations(something.value)
        elif isinstance(something, RefTypeAnnotation):
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
    """Iterate over all the descriptions from the ``something``."""
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


class _PropertyOfClass:
    """Represent the property with its corresponding class."""

    def __init__(self, prop: Property, cls: Class):
        """Initialize with the given values."""
        self.prop = prop
        self.cls = cls


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

    ontology, ontology_errors = _hierarchy.map_symbol_table_to_ontology(
        parsed_symbol_table=parsed_symbol_table
    )
    if ontology_errors is not None:
        underlying_errors.extend(ontology_errors)

    if len(underlying_errors) > 0:
        # If the ontology could not be inferred, we can not perform any error recovery
        # as any further analysis will be invalidated.
        return None, bundle_underlying_errors()

    assert ontology is not None

    # endregion

    # region Understand constructor stacks

    constructor_table, constructor_error = construction.understand_all(
        parsed_symbol_table=parsed_symbol_table, atok=atok)

    if constructor_error is not None:
        underlying_errors.append(constructor_error)

    # endregion

    # region Resolve settings for the JSON serialization

    serializations, serializations_error = _resolve_serializations(
        ontology=ontology, parsed_symbol_table=parsed_symbol_table)

    if serializations_error is not None:
        underlying_errors.append(serializations_error)

    # endregion

    if len(underlying_errors) > 0:
        # We can not proceed and recover from these errors as they concern critical
        # dependencies of the further analysis.
        return None, bundle_underlying_errors()

    # region First pass of translation

    assert constructor_table is not None

    in_lined_constructors = _in_line_constructors(
        parsed_symbol_table=parsed_symbol_table,
        ontology=ontology,
        constructor_table=constructor_table,
    )

    assert serializations is not None

    # Type annotations reference placeholder symbols at this point.

    symbols = []  # type: List[Symbol]
    for parsed_symbol in parsed_symbol_table.symbols:
        symbol = None  # type: Optional[Symbol]

        if isinstance(parsed_symbol, parse.Enumeration):
            symbol = _parsed_enumeration_to_enumeration(parsed=parsed_symbol)

        elif isinstance(parsed_symbol, parse.AbstractClass):
            symbol = _parsed_abstract_class_to_interface(
                parsed=parsed_symbol,
                serializations=serializations)

        elif isinstance(parsed_symbol, parse.ConcreteClass):
            symbol, error = _parsed_class_to_class(
                parsed=parsed_symbol,
                ontology=ontology,
                serializations=serializations,
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

    ref_association = next(
        (
            symbol
            for symbol in symbols
            if symbol.name == parsed_symbol_table.ref_association.name
        ),
        None)

    if ref_association is None:
        raise AssertionError(
            f"The symbol associated with the references has been found in "
            f"the symbol table at the parse stage, "
            f"{parsed_symbol_table.ref_association.name=}, but could not be found "
            f"in the intermediate list of symbols."
        )

    meta_model = MetaModel(
        book_url=parsed_symbol_table.meta_model.book_url,
        book_version=parsed_symbol_table.meta_model.book_version,
        description=_parsed_description_to_description(
            parsed_symbol_table.meta_model.description))

    symbol_table = SymbolTable(
        symbols=symbols,
        ref_association=ref_association,
        meta_model=meta_model)

    # endregion

    # region Second pass to resolve the symbols in the atomic types

    for symbol in symbol_table.symbols:
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
            referenced_symbol = symbol_table.find(identifier)
            if referenced_symbol is None:
                underlying_errors.append(
                    Error(
                        our_type_annotation.parsed.node,
                        f"The symbol with identifier {identifier!r} is not available "
                        f"in the symbol table."))
                continue

            our_type_annotation.symbol = referenced_symbol

    # endregion

    # region Second pass to resolve the symbols in the descriptions

    # If there is no symbol associated with the description, it is set to None.
    symbols_descriptions = [
        (symbol, description)
        for symbol in symbol_table.symbols
        for description in _over_descriptions(symbol)
    ]

    if symbol_table.meta_model.description is not None:
        symbols_descriptions.append((None, symbol_table.meta_model.description))

    for _, description in symbols_descriptions:
        for symbol_ref_in_doc in description.document.traverse(
                condition=SymbolReferenceInDoc):

            # Symbol references can be repeated as docutils will cache them
            # so we need to skip them.
            if not isinstance(symbol_ref_in_doc.symbol, _PlaceholderSymbol):
                continue

            raw_identifier = symbol_ref_in_doc.symbol.identifier
            if not raw_identifier.startswith("."):
                underlying_errors.append(Error(
                    description.node,
                    f"The identifier of the symbol reference "
                    f"is invalid: {raw_identifier}; "
                    f"expected an identifier starting with a dot"))
                continue

            raw_identifier_no_dot = raw_identifier[1:]

            if not IDENTIFIER_RE.match(raw_identifier_no_dot):
                underlying_errors.append(Error(
                    description.node,
                    f"The identifier of the symbol reference "
                    f"is invalid: {raw_identifier_no_dot}"))
                continue

            # Strip the dot
            identifier = Identifier(raw_identifier_no_dot)

            referenced_symbol = symbol_table.find(name=identifier)
            if referenced_symbol is None:
                underlying_errors.append(Error(
                    description.node,
                    f"The identifier of the symbol reference "
                    f"could not be found in the symbol table: {identifier}"))
                continue

            symbol_ref_in_doc.symbol = referenced_symbol

    # endregion

    # region Second pass to resolve the attribute references in the descriptions

    for symbol, description in symbols_descriptions:
        # TODO: test this, especially the failure cases
        for attr_ref_in_doc in description.document.traverse(
                condition=AttributeReferenceInDoc):
            if isinstance(attr_ref_in_doc.reference, _PlaceholderAttributeReference):
                pth = attr_ref_in_doc.reference.path
                parts = pth.split('.')

                if any(not IDENTIFIER_RE.match(part) for part in parts):
                    underlying_errors.append(Error(
                        description.node,
                        f"Invalid reference to a property or a literal; "
                        f"each part of the path needs to be an identifier, "
                        f"but it is not: {pth}"))
                    continue

                part_identifiers = [Identifier(part) for part in parts]

                if len(part_identifiers) == 0:
                    underlying_errors.append(Error(
                        description.node,
                        "Unexpected empty reference "
                        "to a property or a literal"))
                    continue

                # noinspection PyUnusedLocal
                target_symbol = None  # type: Optional[Symbol]

                # noinspection PyUnusedLocal
                attr_identifier = None  # type: Optional[Identifier]

                if len(part_identifiers) == 1:
                    if symbol is None:
                        underlying_errors.append(Error(
                            description.node,
                            f"The attribute reference can not be resolved as there is "
                            f"no encompassing symbol in the given context: {pth}"))
                        continue

                    target_symbol = symbol
                    attr_identifier = part_identifiers[0]
                elif len(part_identifiers) == 2:
                    target_symbol = symbol_table.find(part_identifiers[0])
                    if target_symbol is None:
                        underlying_errors.append(Error(
                            description.node,
                            f"Dangling reference to a non-existing "
                            f"symbol: {pth}"))
                        continue

                    attr_identifier = part_identifiers[1]
                else:
                    underlying_errors.append(Error(
                        description.node,
                        f"We did not implement the resolution of such "
                        f"a reference to a property or a literal: {pth}"))
                    continue

                assert target_symbol is not None
                assert attr_identifier is not None

                reference: Optional[
                    Union[
                        PropertyReferenceInDoc,
                        EnumerationLiteralReferenceInDoc]] = None

                if isinstance(target_symbol, Enumeration):
                    literal = target_symbol.literals_by_name.get(
                        attr_identifier, None)

                    if literal is None:
                        underlying_errors.append(Error(
                            description.node,
                            f"Dangling reference to a non-existing literal "
                            f"in the enumeration {target_symbol.name}: {pth}"))
                        continue

                    reference = EnumerationLiteralReferenceInDoc(
                        symbol=target_symbol, literal=literal)

                elif isinstance(target_symbol, (Class, Interface)):
                    prop = target_symbol.properties_by_name.get(
                        attr_identifier, None)

                    if prop is None:
                        underlying_errors.append(Error(
                            description.node,
                            f"Dangling reference to a non-existing property "
                            f"of a class {target_symbol.name}: {pth}"))
                        continue

                    reference = PropertyReferenceInDoc(
                        symbol=target_symbol, prop=prop)

                else:
                    assert_never(target_symbol)

                assert reference is not None
                attr_ref_in_doc.reference = reference

    # endregion

    # region Second pass to resolve the default argument values

    for symbol in symbol_table.symbols:
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

    # region Second pass to resolve the supersets of the enumerations

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Enumeration):
            continue

        is_superset_of = []  # type: List[Enumeration]
        for placeholder in symbol.is_superset_of:
            assert isinstance(placeholder, _PlaceholderSymbol), (
                f"Expected the subset in a ``is_superset_of`` to be resolved "
                f"only in the second pass for enumeration {symbol.name}, "
                f"but got: {placeholder}")

            referenced_symbol = symbol_table.find(
                name=Identifier(placeholder.identifier))

            if referenced_symbol is None:
                underlying_errors.append(Error(
                    symbol.parsed.node,
                    f"The subset enumeration in ``is_superset_of`` has "
                    f"not been defined: {placeholder.identifier}"))
                continue

            if not isinstance(referenced_symbol, Enumeration):
                underlying_errors.append(Error(
                    symbol.parsed.node,
                    f"An element, {placeholder.identifier}, of ``is_superset_of`` is "
                    f"not an Enumeration, but: {type(referenced_symbol)}"))
                continue

            is_superset_of.append(referenced_symbol)

        for subset_enum in is_superset_of:
            for subset_literal in subset_enum.literals:
                literal = symbol.literals_by_name.get(subset_literal.name, None)
                if literal is None:
                    underlying_errors.append(Error(
                        symbol.parsed.node,
                        f"The literal {subset_literal.name} "
                        f"from the subset enumeration {subset_enum.name} "
                        f"is missing in the enumeration {symbol.name}"))
                    continue

                if literal.value != subset_literal.value:
                    underlying_errors.append(Error(
                        symbol.parsed.node,
                        f"The value {subset_literal.value!r} "
                        f"of the literal {subset_literal.name} "
                        f"from the subset enumeration {subset_enum.name} "
                        f"does not equal the value {literal.value!r} "
                        f"of the literal {literal.name} "
                        f"in the enumeration {symbol.name}"))
                    continue

        symbol.is_superset_of = is_superset_of

    # endregion

    # region Second pass to resolve the interfaces and inheritances

    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        elif isinstance(symbol, Interface):
            resolved_inheritances = []  # type: List[Interface]
            for inheritance in symbol.inheritances:
                assert isinstance(inheritance, _PlaceholderSymbol)

                inheritance_symbol = symbol_table.must_find(
                    Identifier(inheritance.identifier))

                assert isinstance(inheritance_symbol, Interface)

                resolved_inheritances.append(inheritance_symbol)

            symbol.inheritances = resolved_inheritances

        elif isinstance(symbol, Class):
            resolved_interfaces = []  # type: List[Interface]
            for interface in symbol.interfaces:
                assert isinstance(interface, _PlaceholderSymbol)

                interface_symbol = symbol_table.must_find(
                    Identifier(interface.identifier))

                assert isinstance(interface_symbol, Interface)

                resolved_interfaces.append(interface_symbol)

            symbol.interfaces = resolved_interfaces
        else:
            assert_never(symbol)

    # endregion

    # region Second pass to resolve the resulting class of the ``implemented_for``

    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        for prop in symbol.properties:
            assert isinstance(prop.implemented_for, _PlaceholderSymbol), (
                f"Expected the placeholder symbol for ``implemented_for`` in "
                f"the property {prop} of {symbol}, but got: {prop.implemented_for}")

            prop.implemented_for = symbol_table.must_find(
                Identifier(prop.implemented_for.identifier))

    # endregion

    # region Check that all implementers of interfaces have ``with_model_type``

    ids_of_used_interfaces = collect_ids_of_interfaces_in_properties(
        symbol_table=symbol_table)

    interface_implementers = map_interface_implementers(symbol_table=symbol_table)

    for symbol in symbol_table.symbols:
        if (
                isinstance(symbol, Interface)
                and id(symbol) in ids_of_used_interfaces
        ):
            implementers = interface_implementers.get(symbol, None)
            if implementers is not None:
                for implementer in implementers:
                    if not implementer.serialization.with_model_type:
                        underlying_errors.append(Error(
                            implementer.parsed.node,
                            f"The class {implementer.name} needs to have "
                            f"serialization setting ``with_model_type`` set since "
                            f"it is among the concrete classes of "
                            f"the abstract class {symbol.name}. Otherwise, "
                            f"the abstract class {symbol.name} can not be "
                            f"de/serialized properly."
                        ))

    # endregion

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    return symbol_table, None
