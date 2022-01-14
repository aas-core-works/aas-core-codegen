"""Translate the parsed representation into the intermediate representation."""
import ast
import collections
import itertools
import re
from typing import (
    Sequence,
    List,
    Mapping,
    Optional,
    MutableMapping,
    Tuple,
    Union,
    Iterator,
    TypeVar,
    Generic,
    cast,
    Final,
    Type,
    Any,
)

import asttokens
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
from icontract import require, ensure

from aas_core_codegen import parse
from aas_core_codegen.common import (
    Error,
    Identifier,
    assert_never,
    IDENTIFIER_RE,
)
from aas_core_codegen.intermediate import (
    _hierarchy,
    construction,
    doc,
    pattern_verification,
)
from aas_core_codegen.intermediate._types import (
    SymbolTable,
    Enumeration,
    EnumerationLiteral,
    PrimitiveType,
    Argument,
    Default,
    DefaultConstant,
    Property,
    Invariant,
    Contracts,
    Contract,
    Snapshot,
    Serialization,
    Method,
    Class,
    Constructor,
    Symbol,
    ListTypeAnnotation,
    OptionalTypeAnnotation,
    OurTypeAnnotation,
    STR_TO_PRIMITIVE_TYPE,
    PrimitiveTypeAnnotation,
    Description,
    DefaultEnumerationLiteral,
    MetaModel,
    RefTypeAnnotation,
    ImplementationSpecificMethod,
    ImplementationSpecificVerification,
    PatternVerification,
    ConstrainedPrimitive,
    ConcreteClass,
    AbstractClass,
    SignatureLike,
    Interface,
    TypeAnnotationUnion,
    ClassUnion,
    VerificationUnion,
    UnderstoodMethod,
    collect_ids_of_classes_in_properties,
)
from aas_core_codegen.parse import tree as parse_tree


# pylint: disable=unused-argument

# noinspection PyUnusedLocal
def _symbol_reference_role(  # type: ignore
    role, rawtext, text, lineno, inliner, options=None, content=None
) -> Any:
    """Create an element of the description as a reference to a symbol."""
    # See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
    if options is None:
        options = {}

    docutils.parsers.rst.roles.set_classes(options)

    # NOTE (mristin, 2021-12-27):
    # We need to create a placeholder as the symbol table might not be fully created
    # at the point when we translate the documentation.
    #
    # We have to resolve the placeholders in the second pass of the translation with
    # the actual references to the symbol table.

    # noinspection PyTypeChecker
    node = doc.SymbolReference(
        _PlaceholderSymbol(name=text),  # type: ignore
        rawtext,
        docutils.utils.unescape(text),
        refuri=text,
        **options,
    )
    return [node], []


_ATTRIBUTE_REFERENCE_RE = re.compile(
    r"[a-zA-Z_][a-zA-Z_0-9]*(\.[a-zA-Z_][a-zA-Z_0-9]*)?"
)


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
def _attribute_reference_role(  # type: ignore
    role, rawtext, text, lineno, inliner, options=None, content=None
) -> Any:
    """Create a reference in the documentation to a property or a literal."""
    # See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
    if content is None:
        content = []

    if options is None:
        options = {}

    docutils.parsers.rst.roles.set_classes(options)

    # We strip the tilde based on the convention as we ignore the appearance.
    # See: https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#cross-referencing-syntax
    path = text[1:] if text.startswith("~") else text

    # NOTE (mristin, 2021-12-27):
    # We need to create a placeholder as the symbol table might not be fully created
    # at the point when we translate the documentation.
    #
    # We have to resolve the placeholders in the second pass of the translation with
    # the actual references to the symbol table.

    # noinspection PyTypeChecker
    node = doc.AttributeReference(
        _PlaceholderAttributeReference(path=path),  # type: ignore
        rawtext,
        docutils.utils.unescape(text),
        refuri=text,
        **options,
    )
    return [node], []


# noinspection PyUnusedLocal
def _argument_reference_role(  # type: ignore
    role, rawtext, text, lineno, inliner, options=None, content=None
) -> Any:
    """Create a reference in the documentation to a property or a literal."""
    # See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
    if content is None:
        content = []

    if options is None:
        options = {}

    docutils.parsers.rst.roles.set_classes(options)

    reference = text

    node = doc.ArgumentReference(
        reference, rawtext, docutils.utils.unescape(text), refuri=text, **options
    )
    return [node], []


# pylint: enable=unused-argument

# The global registration is unfortunate since it is unpredictable and might affect
# other modules, but it is the only way to register the roles.
#
# See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
docutils.parsers.rst.roles.register_local_role("class", _symbol_reference_role)
docutils.parsers.rst.roles.register_local_role("attr", _attribute_reference_role)
docutils.parsers.rst.roles.register_local_role("paramref", _argument_reference_role)


def _parsed_description_to_description(parsed: parse.Description) -> Description:
    """Translate the parsed description to an intermediate form."""
    # NOTE (mristin, 2021-09-16):
    # This function makes a simple copy at the moment, which might seem pointless.
    #
    # However, we want to explicitly delineate layers (the parse and the intermediate
    # layer, respectively). This simple copying thus helps the understanding
    # of the general system and allows the reader to ignore, to a certain degree, the
    # parse layer when examining the output of the intermediate layer.

    # This run-time check is necessary, we already burned our fingers.
    assert parsed is not None

    return Description(document=parsed.document, node=parsed.node)


class _PlaceholderSymbol:
    """Reference something which will be resolved once the table is built."""

    def __init__(self, name: str) -> None:
        """Initialize with the given values."""
        self.name = name


def _parsed_enumeration_to_enumeration(parsed: parse.Enumeration) -> Enumeration:
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
                    else None
                ),
                parsed=parsed_literal,
            )
            for parsed_literal in parsed.literals
        ],
        # Postpone the resolution to the second pass once the symbol table has been
        # completely built
        is_superset_of=cast(
            List[Enumeration],
            [
                _PlaceholderSymbol(name=identifier)
                for identifier in parsed.is_superset_of
            ],
        ),
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None
        ),
        parsed=parsed,
    )


def _parsed_type_annotation_to_type_annotation(
    parsed: parse.TypeAnnotation,
) -> TypeAnnotationUnion:
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
        primitive_type = STR_TO_PRIMITIVE_TYPE.get(parsed.identifier, None)

        if primitive_type is not None:
            return PrimitiveTypeAnnotation(a_type=primitive_type, parsed=parsed)

        # noinspection PyTypeChecker
        return OurTypeAnnotation(
            symbol=_PlaceholderSymbol(name=parsed.identifier),  # type: ignore
            parsed=parsed,
        )

    elif isinstance(parsed, parse.SubscriptedTypeAnnotation):
        if parsed.identifier == "List":
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the List type annotation, "
                f"but got: {parsed}; this should have been caught before!"
            )

            return ListTypeAnnotation(
                items=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed,
            )

        elif parsed.identifier == "Optional":
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Optional type annotation, "
                f"but got: {parsed}; this should have been caught before!"
            )

            return OptionalTypeAnnotation(
                value=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed,
            )

        elif parsed.identifier == "Ref":
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Ref type annotation, "
                f"but got: {parsed}; this should have been caught before!"
            )

            return RefTypeAnnotation(
                value=_parsed_type_annotation_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed,
            )

        else:
            raise AssertionError(
                f"Unexpected subscripted type annotation identifier: "
                f"{parsed.identifier}. "
                f"This should have been handled or caught before!"
            )

    elif isinstance(parsed, parse.SelfTypeAnnotation):
        raise AssertionError(
            f"Unexpected self type annotation in the intermediate layer: {parsed}"
        )

    else:
        assert_never(parsed)

    raise AssertionError("Should not have gotten here")


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


def _parsed_arguments_to_arguments(parsed: Sequence[parse.Argument]) -> List[Argument]:
    """Translate the arguments of a method in meta-model to the intermediate ones."""
    return [
        Argument(
            name=parsed_arg.name,
            type_annotation=_parsed_type_annotation_to_type_annotation(
                parsed_arg.type_annotation
            ),
            default=_DefaultPlaceholder(parsed=parsed_arg.default)  # type: ignore
            if parsed_arg.default is not None
            else None,
            parsed=parsed_arg,
        )
        for parsed_arg in parsed
        if not isinstance(parsed_arg.type_annotation, parse.SelfTypeAnnotation)
    ]


def _parsed_property_to_property(parsed: parse.Property, cls: parse.Class) -> Property:
    """Translate a parsed property of a class to an intermediate one."""
    # noinspection PyTypeChecker
    return Property(
        name=parsed.name,
        type_annotation=_parsed_type_annotation_to_type_annotation(
            parsed.type_annotation
        ),
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None
        ),
        # NOTE (mristin, 2021-12-26):
        # We can only resolve the ``specified_for`` when the class is actually
        # created. Therefore, we assign here a placeholder and fix it later in a second
        # pass.
        specified_for=_PlaceholderSymbol(cls.name),  # type: ignore
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
@require(
    lambda parsed:
    'self' in parsed.arguments_by_name,
    "Expected ``self`` argument in the ``parsed`` since it is a genuine class method"
)
@require(
    lambda parsed:
    not parsed.verification,
    "Expected only non-verification methods"
)
# fmt: on
def _parsed_method_to_method(
    parsed: Union[parse.UnderstoodMethod, parse.ImplementationSpecificMethod]
) -> Union[UnderstoodMethod, ImplementationSpecificMethod]:
    """Translate the parsed method into an intermediate representation."""
    if isinstance(parsed, parse.ImplementationSpecificMethod):
        return ImplementationSpecificMethod(
            name=parsed.name,
            arguments=_parsed_arguments_to_arguments(parsed=parsed.arguments),
            returns=(
                None
                if parsed.returns is None
                else _parsed_type_annotation_to_type_annotation(parsed.returns)
            ),
            description=(
                _parsed_description_to_description(parsed.description)
                if parsed.description is not None
                else None
            ),
            contracts=_parsed_contracts_to_contracts(parsed.contracts),
            parsed=parsed,
        )
    elif isinstance(parsed, parse.UnderstoodMethod):
        return UnderstoodMethod(
            name=parsed.name,
            arguments=_parsed_arguments_to_arguments(parsed=parsed.arguments),
            returns=(
                None
                if parsed.returns is None
                else _parsed_type_annotation_to_type_annotation(parsed.returns)
            ),
            description=(
                _parsed_description_to_description(parsed.description)
                if parsed.description is not None
                else None
            ),
            contracts=_parsed_contracts_to_contracts(parsed.contracts),
            body=parsed.body,
            parsed=parsed,
        )
    else:
        assert_never(parsed)

    raise AssertionError("Should have never gotten here")


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
                ancestor = parsed_symbol_table.must_find_class(statement.super_name)

                in_lined_of_ancestor = result.get(ancestor, None)

                assert in_lined_of_ancestor is not None, (
                    f"Expected all the constructors of the ancestors "
                    f"of the class {cls.name} to have been in-lined before "
                    f"due to the topological order of classes in the ontology, "
                    f"but the ancestor {ancestor.name} has not had its "
                    f"constructor in-lined yet"
                )

                in_lined.extend(in_lined_of_ancestor)
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


T = TypeVar("T")


class _SettingWithSource(Generic[T]):
    """
    Represent a setting from an inheritance chain.

    For example, a setting for JSON serialization.
    """

    def __init__(self, value: T, source: parse.Class):
        """Initialize with the given values."""
        self.value = value
        self.source = source

    def __repr__(self) -> str:
        return f"_SettingWithSource(value={self.value!r}, source={self.source.name!r})"


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
    ontology: _hierarchy.Ontology, parsed_symbol_table: parse.SymbolTable
) -> Tuple[Optional[MutableMapping[parse.Class, Serialization]], Optional[Error]]:
    """Resolve how general serialization settings stack through the ontology."""
    # NOTE (mristin, 2021-11-03):
    # We do not abstract away different serialization settings at this point
    # as there is only a single one, ``with_model_type``. In the future, if there are
    # more settings, this function needs to be split into multiple ones (one function
    # for a setting each), or maybe we can even think of a more general approach to
    # inheritance of serialization settings.

    # region ``with_model_type``

    with_model_type_map = (
        dict()
    )  # type: MutableMapping[Identifier, Optional[_SettingWithSource[bool]]]

    for parsed_cls in ontology.classes:
        if any(
            parent_name in parse.PRIMITIVE_TYPES
            for parent_name in parsed_cls.inheritances
        ):
            assert len(parsed_cls.inheritances) == 1, (
                f"A constrained primitive type in the initial set should only "
                f"inherit from the primitive type. {parsed_cls.name=}"
            )

            # We can not steer how constrained primitives are serialized as they will be
            # serialized according to their underlying primitive type.

            with_model_type_map[parsed_cls.name] = None
            continue

        assert parsed_cls.name not in with_model_type_map, (
            f"Expected the ontology to be a correctly linearized DAG, "
            f"but the class {parsed_cls.name!r} has been already visited before"
        )

        settings = []  # type: List[_SettingWithSource[bool]]

        if (
            parsed_cls.serialization is not None
            and parsed_cls.serialization.with_model_type
        ):
            settings.append(
                _SettingWithSource(
                    value=parsed_cls.serialization.with_model_type, source=parsed_cls
                )
            )

        for inheritance in parsed_cls.inheritances:
            assert inheritance in with_model_type_map, (
                f"Expected the ontology to be a correctly linearized DAG, "
                f"but the inheritance {inheritance!r} of the class {parsed_cls.name!r} "
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
                        parsed_cls.node,
                        f"The serialization setting ``with_model_type`` "
                        f"between the class {setting.source} "
                        f"and {settings[0].source} is "
                        f"inconsistent",
                    )

        with_model_type_map[parsed_cls.name] = (
            None if len(settings) == 0 else settings[0]
        )

    # endregion

    mapping = dict()  # type: MutableMapping[parse.Class, Serialization]

    for identifier, setting in with_model_type_map.items():
        cls = parsed_symbol_table.must_find_class(name=identifier)
        if setting is None:
            # Neither the current class nor its ancestors specified the setting
            # so we assume the default value.
            mapping[cls] = Serialization(with_model_type=False)
        else:
            mapping[cls] = Serialization(with_model_type=setting.value)

    return mapping, None


# fmt: off
@ensure(
    lambda parsed_symbol_table, result:
    not (result[1] is not None)
    or (
            all(
                isinstance(
                    parsed_symbol_table.must_find_class(identifier),
                    parse.ConcreteClass)
                for identifier in result[1]
            )
    ),
    "Constrained primitive types must be concrete classes"
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _determine_constrained_primitives_by_name(
    parsed_symbol_table: parse.SymbolTable,
    ontology: _hierarchy.Ontology,
) -> Tuple[Optional[MutableMapping[Identifier, PrimitiveType]], Optional[List[Error]]]:
    """
    Determine which classes are constraining a primitive type.

    We also catch errors in case one or more definitions are incorrect.
    For example, if a class that inherits from a primitive type also specifies
    properties or methods.
    """
    # NOTE (mristin, 2021-12-22):
    # We consider two sets of constrained primitives. The first set is
    # the initial set that constraints the primitive. The second set, the extended
    # set, is a set of constrained primitive types which inherit from one or
    # more initial ones.
    #
    # We collect the sets in two passes. We collect the initial set in the first pass.
    # Then, in the second pass, we propagate the "is-constrained-primitive-type"
    # through the class hierarchy.

    errors = []  # type: List[Error]

    initial_map = (
        collections.OrderedDict()
    )  # type: MutableMapping[Identifier, PrimitiveType]

    # region First pass to determine the initial set

    for parsed_symbol in parsed_symbol_table.symbols:
        if not isinstance(parsed_symbol, parse.Class):
            continue

        if any(
            parent in parse.PRIMITIVE_TYPES for parent in parsed_symbol.inheritances
        ):
            if len(parsed_symbol.inheritances) > 1:
                errors.append(
                    Error(
                        parsed_symbol.node,
                        f"The class {parsed_symbol.name!r} constrains "
                        f"a primitive type, but also inherits from other classes: "
                        f"{parsed_symbol.inheritances}. We do not know how to generate "
                        f"an implementation for that.",
                    )
                )
                continue

            assert parsed_symbol.name not in initial_map
            initial_map[parsed_symbol.name] = STR_TO_PRIMITIVE_TYPE[
                parsed_symbol.inheritances[0]
            ]

    if len(errors) > 0:
        return None, errors

    # endregion

    # region Second pass to propagate from the initial set

    # NOTE (mristin, 2021-12-23):
    # Find the connected component from all the classes of the initial set.
    # See https://en.wikipedia.org/wiki/Component_(graph_theory)

    # Put all the descendants of the initial set on the stack
    stack = []  # type: List[Tuple[Identifier, PrimitiveType, Identifier]]

    for identifier_of_the_initial, constrainee_of_the_initial in initial_map.items():
        parsed_cls = parsed_symbol_table.must_find_class(name=identifier_of_the_initial)

        for descendant in ontology.list_descendants(parsed_cls):
            stack.append(
                (descendant.name, constrainee_of_the_initial, identifier_of_the_initial)
            )

    # Propagate the constrainees through the ontology

    # Map: identifier 🠒 determined primitive type, the ancestor which determined it
    extended_map = (
        collections.OrderedDict()
    )  # type: MutableMapping[Identifier, Tuple[PrimitiveType, Identifier]]

    while len(stack) > 0 and len(errors) == 0:
        # NOTE (mristin, 2021-12-23):
        # Since we operate on the ontology, we know that the cycles in the inheritance
        # graph would have been already reported as errors and we would not get
        # thus far.

        identifier, constrainee, ancestor = stack.pop()
        parsed_cls = parsed_symbol_table.must_find_class(name=identifier)

        already_determined_constrainee_and_another_ancestor = extended_map.get(
            identifier, None
        )

        if already_determined_constrainee_and_another_ancestor is not None:
            (
                already_determined_constrainee,
                another_ancestor,
            ) = already_determined_constrainee_and_another_ancestor

            if (
                already_determined_constrainee is not None
                and already_determined_constrainee != constrainee
            ):
                errors.append(
                    Error(
                        parsed_cls.node,
                        f"The primitive type of the constrained primitive type "
                        f"{identifier!r} can not be resolved. The ancestor "
                        f"{ancestor!r} specifies {constrainee.value!r}, while "
                        f"another ancestor, {another_ancestor!r}, specifies "
                        f"{already_determined_constrainee.value!r}",
                    )
                )

        else:
            extended_map[identifier] = (constrainee, ancestor)

        for descendant in ontology.list_descendants(parsed_cls):
            stack.append((descendant.name, constrainee, identifier))

    if len(errors) > 0:
        return None, errors

    # endregion

    # region Convert the initial and extended map into one

    result = (
        collections.OrderedDict()
    )  # type: MutableMapping[Identifier, PrimitiveType]

    for identifier, constrainee in initial_map.items():
        result[identifier] = constrainee

    for identifier, (constrainee, _) in extended_map.items():
        result[identifier] = constrainee

    # endregion

    # region Check the inheritances of all the constrained primitive types

    # BEFORE-RELEASE (mristin, 2021-12-23): test this
    for identifier in extended_map.keys():
        # We know for sure that the initial set is valid so we can skip it in the check.
        if identifier in initial_map:
            continue

        parsed_cls = parsed_symbol_table.must_find_class(name=identifier)

        # Make sure that the constrained primitive types only inherit from other
        # constrained primitive types

        constrained_inheritances = []  # type: List[Identifier]
        unexpected_inheritances = []  # type: List[Identifier]

        for inheritance in parsed_cls.inheritances:
            if inheritance not in result:
                unexpected_inheritances.append(inheritance)
            else:
                constrained_inheritances.append(inheritance)

        if len(unexpected_inheritances) > 0:
            constrained_inheritances_str = ", ".join(
                repr(identifier) for identifier in constrained_inheritances
            )

            unexpected_inheritances_str = ", ".join(
                repr(identifier) for identifier in unexpected_inheritances
            )
            errors.append(
                Error(
                    parsed_cls.node,
                    f"The class {parsed_cls.name} inherits both from one or more "
                    f"constrained primitive types ({constrained_inheritances_str}), "
                    f"but also other classes which are not constraining primitive "
                    f"types ({unexpected_inheritances_str}).",
                )
            )

    if len(errors) > 0:
        return None, errors

    # endregion

    # region Check that primitive types do not have unexpected specification

    # BEFORE-RELEASE (mristin, 2021-12-23): test this
    for identifier in result:
        parsed_cls = parsed_symbol_table.must_find_class(identifier)
        if len(parsed_cls.methods) > 0 or len(parsed_cls.properties) > 0:
            errors.append(
                Error(
                    parsed_cls.node,
                    f"The class {parsed_cls.name!r} constrains a primitive type, "
                    f"but also specifies properties and/or methods. "
                    f"We do not know how to generate an implementation for that.",
                )
            )

        if parsed_cls.serialization is not None:
            errors.append(
                Error(
                    parsed_cls.node,
                    f"The class {parsed_cls.name!r} constrains a primitive type, "
                    f"but the serialization settings are set. We must "
                    f"serialize it as a primitive type and no custom serialization "
                    f"settings are possible.",
                )
            )

        if isinstance(parsed_cls, parse.AbstractClass):
            errors.append(
                Error(
                    parsed_cls.node,
                    f"The class {parsed_cls.name!r} constrains a primitive type, "
                    f"but it is denoted abstract. Every value that "
                    f"fulfills the constraints can be instantiated, so it can not be "
                    f"made abstract.",
                )
            )

    # endregion

    return result, None


def _stack_invariants(
    ontology: _hierarchy.Ontology,
) -> MutableMapping[Identifier, List[Invariant]]:
    """Determine invariants for all the classes by stacking them from the ancestors."""
    invariants_map = (
        collections.OrderedDict()
    )  # type: MutableMapping[Identifier, List[Invariant]]

    for parsed_cls in ontology.classes:
        # NOTE (mristin, 2021-12-14):
        # We assume here that classes in the ontology are sorted
        # in the topological order.

        invariants = invariants_map.get(parsed_cls.name, None)
        if invariants is None:
            invariants = []
            invariants_map[parsed_cls.name] = invariants

        # noinspection PyTypeChecker
        invariants.extend(
            Invariant(
                description=parsed_invariant.description,
                body=parsed_invariant.body,
                specified_for=_PlaceholderSymbol(parsed_cls.name),  # type: ignore
                parsed=parsed_invariant,
            )
            for parsed_invariant in parsed_cls.invariants
        )

        # Propagate all the invariants to the descendants

        for descendant in ontology.list_descendants(parsed_cls):
            descendant_invariants = invariants_map.get(descendant.name, None)

            if descendant_invariants is None:
                descendant_invariants = []
                invariants_map[descendant.name] = descendant_invariants

            descendant_invariants.extend(invariants)

    return invariants_map


def _parsed_class_to_constrained_primitive(
    parsed: parse.ConcreteClass,
    constrainee: PrimitiveType,
    invariants: Sequence[Invariant],
) -> ConstrainedPrimitive:
    """
    Translate a concrete class to a constrained primitive.

    The ``parsed`` is expected to be tested for being a valid constrained primitive
    before calling this function.

    The ``constrainee`` is determined by propagation in
    :py:function:`_determine_constrained_primitives_by_name`.

    The ``invariants`` are determined by stacking in
    :py:function:`_stack_invariants`.
    """
    # noinspection PyTypeChecker
    return ConstrainedPrimitive(
        name=parsed.name,
        # Use placeholders for inheritances and descendants as we are still in
        # the first pass and building up the symbol table. They will be resolved in
        # a second pass.
        inheritances=[],
        descendants=[],
        constrainee=constrainee,
        is_implementation_specific=parsed.is_implementation_specific,
        invariants=invariants,
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None
        ),
        parsed=parsed,
    )


class _MaybeInterfacePlaceholder:
    """
    Represent a placeholder for the interfaces.

    We do not know in the first pass whether a class will have an interface defined
    or not.
    """


def _parsed_class_to_class(
    parsed: parse.ClassUnion,
    ontology: _hierarchy.Ontology,
    serializations: Mapping[parse.Class, Serialization],
    invariants: Sequence[Invariant],
    in_lined_constructors: Mapping[parse.Class, Sequence[construction.AssignArgument]],
) -> ClassUnion:
    """
    Translate a concrete parsed class to an intermediate class.

    The ``invariants`` are determined by stacking in
    :py:function:`_stack_invariants`.
    """
    ancestors = ontology.list_ancestors(cls=parsed)

    # region Stack properties from the ancestors

    # BEFORE-RELEASE (mristin, 2021-12-14):
    #  We need to refactor this function since it is now running in quadratic time
    #  for properties, methods and constructors. We just have to follow the same trick
    #  as with ``_stack_invariants``, but we have to be careful not to miss one or the
    #  other important detail.

    properties = []  # type: List[Property]

    # We explicitly check that there are no property overloads at the parse stage so
    # we do not perform the same check here for the second time.

    for ancestor in ancestors:
        properties.extend(
            _parsed_property_to_property(parsed=parsed_prop, cls=ancestor)
            for parsed_prop in ancestor.properties
        )

    for parsed_prop in parsed.properties:
        properties.append(_parsed_property_to_property(parsed=parsed_prop, cls=parsed))

    # endregion

    # region Stack constructors from the ancestors

    contracts = Contracts(preconditions=[], snapshots=[], postconditions=[])

    for ancestor in ancestors:
        parsed_ancestor_init = ancestor.methods_by_name.get(
            Identifier("__init__"), None
        )

        if parsed_ancestor_init is not None:
            contracts = _stack_contracts(
                contracts,
                _parsed_contracts_to_contracts(parsed_ancestor_init.contracts),
            )

    arguments = []
    init_is_implementation_specific = False

    parsed_class_init = parsed.methods_by_name.get(Identifier("__init__"), None)
    if parsed_class_init is not None:
        arguments = _parsed_arguments_to_arguments(parsed=parsed_class_init.arguments)

        init_is_implementation_specific = isinstance(
            parsed_class_init, parse.ImplementationSpecificMethod
        )

        contracts = _stack_contracts(
            contracts, _parsed_contracts_to_contracts(parsed_class_init.contracts)
        )

    ctor = Constructor(
        is_implementation_specific=init_is_implementation_specific,
        arguments=arguments,
        contracts=contracts,
        description=(
            (
                _parsed_description_to_description(parsed_class_init.description)
                if parsed_class_init.description is not None
                else None
            )
            if parsed_class_init is not None
            else None
        ),
        statements=in_lined_constructors[parsed],
        parsed=(parsed_class_init if parsed_class_init is not None else None),
    )

    # endregion

    # region Stack methods from the ancestors

    methods = []  # type: List[Method]

    # We explicitly check that there are no method overloads at the parse stage
    # so we do not perform this check for the second time here.

    for ancestor in ancestors:
        methods.extend(
            _parsed_method_to_method(parsed=parsed_method)
            for parsed_method in ancestor.methods
            if isinstance(
                parsed_method, (parse.UnderstoodMethod, ImplementationSpecificMethod)
            )
        )

    for parsed_method in parsed.methods:
        if not isinstance(
            parsed_method, (parse.UnderstoodMethod, ImplementationSpecificMethod)
        ):
            # Constructors are in-lined and handled in a different way through
            # :py:class:`Constructors`.
            continue

        methods.append(_parsed_method_to_method(parsed=parsed_method))

    # endregion

    factory_to_use = None  # type: Optional[Type[Class]]

    if isinstance(parsed, parse.ConcreteClass):
        factory_to_use = ConcreteClass
    elif isinstance(parsed, parse.AbstractClass):
        factory_to_use = AbstractClass
    else:
        assert_never(parsed)

    assert factory_to_use is not None

    # noinspection PyTypeChecker
    return factory_to_use(
        name=parsed.name,
        # Use a placeholder for inheritances, descendants and the interface as we can
        # not resolve inheritances at this point
        inheritances=[],
        interface=_MaybeInterfacePlaceholder(),  # type: ignore
        descendants=[],
        is_implementation_specific=parsed.is_implementation_specific,
        properties=properties,
        methods=methods,
        constructor=ctor,
        invariants=invariants,
        serialization=serializations[parsed],
        description=(
            _parsed_description_to_description(parsed.description)
            if parsed.description is not None
            else None
        ),
        parsed=parsed,
    )


# fmt: off
@require(
    lambda parsed:
    parsed.verification, "Expected a verification function"
)
@require(
    lambda parsed:
    'self' not in parsed.arguments_by_name,
    "Expected no ``self`` in the arguments since a verification function should not be "
    "a method of a class"
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _parsed_verification_function_to_verification_function(
    parsed: parse.FunctionUnion,
) -> Tuple[Optional[VerificationUnion], Optional[Error]]:
    """Translate the verification function and try to understand it, if necessary."""
    name = parsed.name
    arguments = _parsed_arguments_to_arguments(parsed=parsed.arguments)
    returns = (
        None
        if parsed.returns is None
        else _parsed_type_annotation_to_type_annotation(parsed.returns)
    )
    description = (
        _parsed_description_to_description(parsed.description)
        if parsed.description is not None
        else None
    )
    contracts = _parsed_contracts_to_contracts(parsed.contracts)

    if isinstance(parsed, parse.ImplementationSpecificMethod):
        return (
            ImplementationSpecificVerification(
                name=name,
                arguments=arguments,
                returns=returns,
                description=description,
                contracts=contracts,
                parsed=parsed,
            ),
            None,
        )

    elif isinstance(parsed, parse.UnderstoodMethod):
        pattern, ok_error, fatal_error = pattern_verification.try_to_understand(
            parsed=parsed
        )

        if fatal_error is not None:
            return None, fatal_error

        # NOTE (mristin, 2021-01-02):
        # Since we only have a single rule, we also return an ``ok_error`` as critical
        # error to explain the user what we could not match. In the future, when
        # there are more rules, we should trace all the "ok" errors and explain why
        # *each single rule* did not match so that the user can debug their verification
        # functions.

        if ok_error is not None:
            return (
                None,
                Error(
                    parsed.node,
                    f"We do not know how to interpret the verification function {name!r} "
                    f"as it does not match our pre-defined interpretation rules. "
                    f"Please contact the developers if you expect this function "
                    f"to be understood.",
                    [ok_error],
                ),
            )

        assert pattern is not None

        return (
            PatternVerification(
                name=name,
                arguments=arguments,
                returns=returns,
                description=description,
                contracts=contracts,
                pattern=pattern,
                parsed=parsed,
            ),
            None,
        )

    elif isinstance(parsed, parse.ConstructorToBeUnderstood):
        return (
            None,
            Error(parsed.node, "Unexpected constructor as a verification function"),
        )
    else:
        assert_never(parsed)

    raise AssertionError("Should not have gotten here")


def _over_our_type_annotations(
    something: Union[Symbol, TypeAnnotationUnion]
) -> Iterator[OurTypeAnnotation]:
    """Iterate over all the atomic type annotations in the ``something``."""
    if isinstance(something, PrimitiveTypeAnnotation):
        pass

    elif isinstance(something, OurTypeAnnotation):
        yield something

    elif isinstance(something, ListTypeAnnotation):
        yield from _over_our_type_annotations(something.items)

    elif isinstance(something, OptionalTypeAnnotation):
        yield from _over_our_type_annotations(something.value)

    elif isinstance(something, RefTypeAnnotation):
        yield from _over_our_type_annotations(something.value)

    elif isinstance(something, Enumeration):
        pass

    elif isinstance(something, ConstrainedPrimitive):
        pass

    elif isinstance(something, Class):
        for prop in something.properties:
            yield from _over_our_type_annotations(prop.type_annotation)

        for method in something.methods:
            for argument in method.arguments:
                yield from _over_our_type_annotations(argument.type_annotation)

            if method.returns is not None:
                yield from _over_our_type_annotations(method.returns)

        for argument in something.constructor.arguments:
            yield from _over_our_type_annotations(argument.type_annotation)

    else:
        assert_never(something)


def _second_pass_to_resolve_symbols_in_atomic_types_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Resolve the symbol references in the atomic types in-place."""
    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        for our_type_annotation in _over_our_type_annotations(symbol):
            assert isinstance(
                our_type_annotation.symbol, _PlaceholderSymbol
            ), "Expected only placeholder symbols to be assigned in the first pass"

            if not IDENTIFIER_RE.match(our_type_annotation.symbol.name):
                errors.append(
                    Error(
                        our_type_annotation.parsed.node,
                        f"The symbol is invalid: "
                        f"{our_type_annotation.symbol.name!r}",
                    )
                )
                continue

            identifier = Identifier(our_type_annotation.symbol.name)
            referenced_symbol = symbol_table.find(identifier)
            if referenced_symbol is None:
                errors.append(
                    Error(
                        our_type_annotation.parsed.node,
                        f"The symbol with identifier {identifier!r} is not available "
                        f"in the symbol table.",
                    )
                )
                continue

            our_type_annotation.symbol = referenced_symbol

    return errors


def _over_descriptions_in_symbol(symbol: Symbol) -> Iterator[Description]:
    """Iterate over all the descriptions from the ``something``."""
    if isinstance(symbol, Enumeration):
        if symbol.description is not None:
            yield symbol.description

        for literal in symbol.literals:
            if literal.description is not None:
                yield literal.description

    elif isinstance(symbol, ConstrainedPrimitive):
        if symbol.description is not None:
            yield symbol.description

    elif isinstance(symbol, Class):
        if symbol.description is not None:
            yield symbol.description

        for prop in symbol.properties:
            if prop.description is not None:
                yield prop.description

        for method in symbol.methods:
            if method.description is not None:
                yield method.description

    elif isinstance(symbol, Description):
        for node in symbol.document.traverse(condition=doc.SymbolReference):
            yield node
    else:
        assert_never(symbol)


def _over_descriptions(
    symbol_table: SymbolTable,
) -> Iterator[Tuple[Optional[Symbol], Description]]:
    """
    Iterate over all the descriptions in the meta-model.

    The symbol indicates the symbol that encompasses the description (*e.g.*
    a class if the description is related to a member or a property). This gives,
    for example, the context when we have to resolve references in the downstream code.
    """
    for symbol in symbol_table.symbols:
        for description in _over_descriptions_in_symbol(symbol):
            yield symbol, description

    for verification in symbol_table.verification_functions:
        if verification.description is not None:
            yield None, verification.description

    if symbol_table.meta_model.description is not None:
        yield None, symbol_table.meta_model.description


def _second_pass_to_resolve_symbol_references_in_the_descriptions_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Resolve the symbol references in the descriptions in-place."""
    errors = []  # type: List[Error]

    for _, description in _over_descriptions(symbol_table):
        for symbol_ref_in_doc in description.document.findall(
            condition=doc.SymbolReference
        ):

            # Symbol references can be repeated as docutils will cache them
            # so we need to skip them.
            if not isinstance(symbol_ref_in_doc.symbol, _PlaceholderSymbol):
                continue

            raw_identifier = symbol_ref_in_doc.symbol.name
            if not raw_identifier.startswith("."):
                errors.append(
                    Error(
                        description.node,
                        f"The identifier of the symbol reference "
                        f"is invalid: {raw_identifier}; "
                        f"expected an identifier starting with a dot",
                    )
                )
                continue

            raw_identifier_no_dot = raw_identifier[1:]

            if not IDENTIFIER_RE.match(raw_identifier_no_dot):
                errors.append(
                    Error(
                        description.node,
                        f"The identifier of the symbol reference "
                        f"is invalid: {raw_identifier_no_dot}",
                    )
                )
                continue

            # Strip the dot
            identifier = Identifier(raw_identifier_no_dot)

            referenced_symbol = symbol_table.find(name=identifier)
            if referenced_symbol is None:
                errors.append(
                    Error(
                        description.node,
                        f"The identifier of the symbol reference "
                        f"could not be found in the symbol table: {identifier}",
                    )
                )
                continue

            symbol_ref_in_doc.symbol = referenced_symbol

    return errors


def _second_pass_to_resolve_attribute_references_in_the_descriptions_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Resolve the attribute references in the descriptions in-place."""
    errors = []  # type: List[Error]

    # The ``symbol`` is None if the description is in the context outside of a symbol.
    for symbol, description in _over_descriptions(symbol_table):
        # BEFORE-RELEASE (mristin, 2021-12-13):
        #  test this, especially the failure cases
        for attr_ref_in_doc in description.document.findall(
            condition=doc.AttributeReference
        ):
            if isinstance(attr_ref_in_doc.reference, _PlaceholderAttributeReference):
                pth = attr_ref_in_doc.reference.path
                parts = pth.split(".")

                if any(not IDENTIFIER_RE.match(part) for part in parts):
                    errors.append(
                        Error(
                            description.node,
                            f"Invalid reference to a property or a literal; "
                            f"each part of the path needs to be an identifier, "
                            f"but it is not: {pth}",
                        )
                    )
                    continue

                part_identifiers = [Identifier(part) for part in parts]

                if len(part_identifiers) == 0:
                    errors.append(
                        Error(
                            description.node,
                            "Unexpected empty reference " "to a property or a literal",
                        )
                    )
                    continue

                # noinspection PyUnusedLocal
                target_symbol = None  # type: Optional[Symbol]

                # noinspection PyUnusedLocal
                attr_identifier = None  # type: Optional[Identifier]

                if len(part_identifiers) == 1:
                    if symbol is None:
                        errors.append(
                            Error(
                                description.node,
                                f"The attribute reference can not be resolved as there "
                                f"is no encompassing symbol in the given "
                                f"context: {pth}",
                            )
                        )
                        continue

                    target_symbol = symbol
                    attr_identifier = part_identifiers[0]
                elif len(part_identifiers) == 2:
                    target_symbol = symbol_table.find(part_identifiers[0])
                    if target_symbol is None:
                        errors.append(
                            Error(
                                description.node,
                                f"Dangling reference to a non-existing "
                                f"symbol: {pth}",
                            )
                        )
                        continue

                    attr_identifier = part_identifiers[1]
                else:
                    errors.append(
                        Error(
                            description.node,
                            f"We did not implement the resolution of such "
                            f"a reference to a property or a literal: {pth}",
                        )
                    )
                    continue

                assert target_symbol is not None
                assert attr_identifier is not None

                reference: Optional[
                    Union[doc.PropertyReference, doc.EnumerationLiteralReference]
                ] = None

                if isinstance(target_symbol, Enumeration):
                    literal = target_symbol.literals_by_name.get(attr_identifier, None)

                    if literal is None:
                        errors.append(
                            Error(
                                description.node,
                                f"Dangling reference to a non-existing literal "
                                f"in the enumeration {target_symbol.name!r}: {pth}",
                            )
                        )
                        continue

                    reference = doc.EnumerationLiteralReference(
                        symbol=target_symbol, literal=literal
                    )

                elif isinstance(target_symbol, ConstrainedPrimitive):
                    errors.append(
                        Error(
                            description.node,
                            f"Unexpected references to a property of "
                            f"a constrained primitive {target_symbol.name!r}: {pth}",
                        )
                    )
                    continue

                elif isinstance(target_symbol, Class):
                    prop = target_symbol.properties_by_name.get(attr_identifier, None)

                    if prop is None:
                        errors.append(
                            Error(
                                description.node,
                                f"Dangling reference to a non-existing property "
                                f"of a class {target_symbol.name!r}: {pth}",
                            )
                        )
                        continue

                    reference = doc.PropertyReference(cls=target_symbol, prop=prop)

                else:
                    assert_never(target_symbol)

                assert reference is not None
                attr_ref_in_doc.reference = reference

    return errors


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _fill_in_default_placeholder(
    default: _DefaultPlaceholder, symbol_table: SymbolTable
) -> Tuple[Optional[Default], Optional[Error]]:
    """Resolve the default values to references using the constructed symbol table."""
    # If we do not preemptively return, signal that we do not know how to handle
    # the default

    if isinstance(default.parsed.node, ast.Constant):
        if (
            isinstance(default.parsed.node.value, (bool, int, float, str))
            or default.parsed.node.value is None
        ):
            return (
                DefaultConstant(value=default.parsed.node.value, parsed=default.parsed),
                None,
            )

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
                return (
                    DefaultEnumerationLiteral(
                        enumeration=symbol, literal=literal, parsed=default.parsed
                    ),
                    None,
                )

    return None, Error(
        default.parsed.node,
        f"The translation of the default value to the intermediate layer "
        f"has not been implemented: {ast.dump(default.parsed.node)}",
    )


def _over_arguments(symbol_table: SymbolTable) -> Iterator[Argument]:
    """Iterate over all the instances of ``Argument`` from the ``symbol_table``."""
    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        elif isinstance(symbol, ConstrainedPrimitive):
            continue

        elif isinstance(symbol, Class):
            for method in symbol.methods:
                yield from method.arguments

            yield from symbol.constructor.arguments
        else:
            assert_never(symbol)

    for verification in symbol_table.verification_functions:
        yield from verification.arguments


def _second_pass_to_resolve_default_argument_values_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Resolve the default values of the method and function arguments in-place."""
    errors = []  # type: List[Error]

    for arg in _over_arguments(symbol_table):
        if arg.default is None:
            continue

        assert isinstance(arg.default, _DefaultPlaceholder), (
            f"Expected the argument default value to be a placeholder "
            f"since we resolve it only in the second pass, "
            f"but got: {arg.default}"
        )

        filled_default, error = _fill_in_default_placeholder(
            default=arg.default, symbol_table=symbol_table
        )

        if error:
            errors.append(error)
        else:
            # NOTE (mristin, 2021-12-26):
            # We can only resolve the default values now since, for example, we would
            # not know how to resolve the references to enumeration literals.
            # The attribute ``default`` is marked final only for the users of the
            # ``intermediate`` module, not for the translation itself.

            # noinspection PyFinal,PyTypeHints
            arg.default = filled_default

    return errors


def _second_pass_to_resolve_supersets_of_enumerations_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Resolve the enumeration references in the supersets in-place."""
    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Enumeration):
            continue

        is_superset_of = []  # type: List[Enumeration]
        for placeholder in symbol.is_superset_of:
            assert isinstance(placeholder, _PlaceholderSymbol), (
                f"Expected the subset in a ``is_superset_of`` to be resolved "
                f"only in the second pass for enumeration {symbol.name}, "
                f"but got: {placeholder}"
            )

            referenced_symbol = symbol_table.find(name=Identifier(placeholder.name))

            if referenced_symbol is None:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"The subset enumeration in ``is_superset_of`` has "
                        f"not been defined: {placeholder.name}",
                    )
                )
                continue

            if not isinstance(referenced_symbol, Enumeration):
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"An element, {placeholder.name}, of ``is_superset_of`` is "
                        f"not an Enumeration, but: {type(referenced_symbol)}",
                    )
                )
                continue

            is_superset_of.append(referenced_symbol)

        for subset_enum in is_superset_of:
            for subset_literal in subset_enum.literals:
                literal = symbol.literals_by_name.get(subset_literal.name, None)
                if literal is None:
                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The literal {subset_literal.name} "
                            f"from the subset enumeration {subset_enum.name} "
                            f"is missing in the enumeration {symbol.name}",
                        )
                    )
                    continue

                if literal.value != subset_literal.value:
                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The value {subset_literal.value!r} "
                            f"of the literal {subset_literal.name} "
                            f"from the subset enumeration {subset_enum.name} "
                            f"does not equal the value {literal.value!r} "
                            f"of the literal {literal.name} "
                            f"in the enumeration {symbol.name}",
                        )
                    )
                    continue

        # NOTE (mristin, 2021-12-27):
        # We could not resolve which enumerations this enumeration is the superset of
        # in the first pass as we still did not instantiate all the symbols while we
        # were building. That is why we have to set it here. The qualifier
        # ``Final[...]`` hints at the clients of the intermediate stage, not at the code
        # during the translation.

        # noinspection PyFinal,PyTypeHints
        symbol.is_superset_of = is_superset_of  # type: ignore

    return errors


def _second_pass_to_resolve_resulting_class_of_specified_for(
    symbol_table: SymbolTable,
) -> None:
    """Resolve the resulting class of the ``specified_for`` in a property in-place."""
    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        elif isinstance(symbol, ConstrainedPrimitive):
            continue

        elif isinstance(symbol, Class):
            for prop in symbol.properties:
                assert isinstance(prop.specified_for, _PlaceholderSymbol), (
                    f"Expected the placeholder symbol for ``specified_for`` in "
                    f"the property {prop} of {symbol}, but got: {prop.specified_for}"
                )

                prop.specified_for = symbol_table.must_find(
                    Identifier(prop.specified_for.name)
                )
        else:
            assert_never(symbol)


def _second_pass_to_resolve_specified_for_in_invariants(
    symbol_table: SymbolTable,
) -> None:
    """Resolve the symbol of the ``specified_for`` of an invariant in-place."""
    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        elif isinstance(symbol, (ConstrainedPrimitive, Class)):
            for invariant in symbol.invariants:
                # NOTE (mristin, 2022-01-02):
                # Since we stack invariants, it might be that we already resolved
                # the invariants coming from the parent. Hence we need to check that
                # we haven't resolved ``specified_for`` here.

                if isinstance(invariant.specified_for, _PlaceholderSymbol):
                    symbol = symbol_table.must_find(
                        Identifier(invariant.specified_for.name)
                    )

                    assert isinstance(symbol, (ConstrainedPrimitive, Class)), (
                        f"Expected the ``specified_for`` of an invariant to be either "
                        f"a constrained primitive or a class, but got: {symbol}"
                    )

                    # NOTE (mristin, 2022-01-02):
                    # We have to override the ``specified_for`` as we could not set it
                    # during the first pass of the translation phase. The ``Final`` in
                    # this context is meant for the users of the translation phase, not
                    # the translation phase itself.

                    # noinspection PyFinal
                    invariant.specified_for = symbol

        else:
            assert_never(symbol)


# fmt: off
@require(
    lambda symbol_table:
    # These are not tight pre-conditions, but they should catch the most obvious
    # bugs, such as if we re-enter this function.
    all(
        isinstance(symbol.inheritances, list)
        and len(symbol.inheritances) == 0
        for symbol in symbol_table.symbols
        if isinstance(symbol, (ConstrainedPrimitive, Class))
    ),
    "No inheritances previously resolved"
)
# fmt: on
def _second_pass_to_resolve_inheritances_in_place(symbol_table: SymbolTable) -> None:
    """Resolve the class references in the class inheritances in-place."""
    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        elif isinstance(symbol, ConstrainedPrimitive):
            resolved_constrained_primitive_inheritances = (
                []
            )  # type: List[ConstrainedPrimitive]

            for inheritance_name in symbol.parsed.inheritances:
                # NOTE (mristin, 2021-12-26):
                # The constrainee is stored at a different property and is not included
                # in the inheritances. The inheritances refer only to ancestor
                # constrained primitives.
                if inheritance_name in parse.PRIMITIVE_TYPES:
                    continue

                inheritance_symbol = symbol_table.must_find(
                    Identifier(inheritance_name)
                )

                assert isinstance(inheritance_symbol, ConstrainedPrimitive)

                resolved_constrained_primitive_inheritances.append(inheritance_symbol)

            symbol._set_inheritances(resolved_constrained_primitive_inheritances)

        elif isinstance(symbol, Class):
            resolved_class_inheritances = []  # type: List[ClassUnion]

            for inheritance_name in symbol.parsed.inheritances:
                inheritance_symbol = symbol_table.must_find(
                    Identifier(inheritance_name)
                )

                assert isinstance(inheritance_symbol, Class)
                resolved_class_inheritances.append(inheritance_symbol)

            symbol._set_inheritances(resolved_class_inheritances)

        else:
            assert_never(symbol)


# fmt: off
@require(
    lambda symbol_table:
    all(
        # These are not tight pre-conditions, but they should catch the most obvious
        # bugs, such as if we re-enter this function.
        isinstance(symbol.concrete_descendants, list) and
        len(symbol.concrete_descendants) == 0
        for symbol in symbol_table.symbols
        if isinstance(symbol, Class)
    )
)
# fmt: on
def _second_pass_to_resolve_descendants_in_place(
    symbol_table: SymbolTable, ontology: _hierarchy.Ontology
) -> None:
    """
    Resolve placeholders for concrete descendants in the classes in-place.

    All abstract classes as well as concrete classes with at least one descendant
    are mapped to an interface.

    Mind that the concept of the interface is not used in the meta-model and we
    introduce it only as a convenience for the code generation.
    """
    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            pass

        elif isinstance(symbol, ConstrainedPrimitive):
            constrained_primitive_descendants = []  # type: List[ConstrainedPrimitive]
            for descendant in ontology.list_descendants(symbol.parsed):
                symbol = symbol_table.must_find(descendant.name)
                assert isinstance(symbol, ConstrainedPrimitive)
                constrained_primitive_descendants.append(symbol)

            symbol._set_descendants(constrained_primitive_descendants)

        elif isinstance(symbol, Class):
            class_descendants = []  # type: List[ClassUnion]
            for descendant in ontology.list_descendants(symbol.parsed):
                descendant_symbol = symbol_table.must_find(descendant.name)
                assert isinstance(descendant_symbol, (AbstractClass, ConcreteClass))
                class_descendants.append(descendant_symbol)

            symbol._set_descendants(class_descendants)

        else:
            assert_never(symbol)


# fmt: off
@require(
    lambda symbol_table:
    all(
        isinstance(symbol.interface, _MaybeInterfacePlaceholder)
        for symbol in symbol_table.symbols
        if isinstance(symbol, Class)
    ),
    "None of the interfaces resolved"
)
@ensure(
    lambda symbol_table:
    all(
        # Exhaustive pattern matching
        isinstance(symbol, (AbstractClass, ConcreteClass))
        and (
                not isinstance(symbol, AbstractClass)
                or isinstance(symbol.interface, Interface)
        )
        and (
                not isinstance(symbol, ConcreteClass)
                or (
                        symbol.interface is None
                        or isinstance(symbol.interface, Interface)
                )
        )
        for symbol in symbol_table.symbols
        if isinstance(symbol, Class)
    ),
    "All interfaces resolved"
)
# fmt: on
def _second_pass_to_resolve_interfaces_in_place(
    symbol_table: SymbolTable, ontology: _hierarchy.Ontology
) -> None:
    """
    Resolve interface placeholders in the classes in-place.

    All abstract classes as well as concrete classes with at least one descendant
    are mapped to an interface.

    Mind that the concept of the interface is not used in the meta-model and we
    introduce it only as a convenience for the code generation.
    """
    for parsed_cls in ontology.classes:
        cls = symbol_table.must_find(parsed_cls.name)

        assert cls.parsed is parsed_cls
        assert isinstance(cls, (ConstrainedPrimitive, Class))

        if isinstance(cls, ConstrainedPrimitive):
            # Constrained primitives do not provide an interface as their interface
            # is the interface of their constrainee.
            continue

        # Make sure we covered all the cases in the if-statement below
        assert isinstance(cls, (AbstractClass, ConcreteClass))

        assert isinstance(cls.interface, _MaybeInterfacePlaceholder), (
            f"Expected the class {cls.name!r} to have a placeholder as an interface, "
            f"but got: {cls.interface!r}"
        )

        if (
            isinstance(cls, AbstractClass)
            or len(ontology.list_descendants(parsed_cls)) > 0
        ):
            parent_interfaces = []  # type: List[Interface]

            for inheritance_name in parsed_cls.inheritances:
                parent_cls = symbol_table.must_find(inheritance_name)

                parent_interface = parent_cls.interface
                assert isinstance(parent_interface, Interface), (
                    f"We expect the classes in the ontology to be topologically "
                    f"sorted. Hence the interface for the parent {inheritance_name!r} "
                    f"of the class {parsed_cls.name!r} must have been defined, but "
                    f"it was not: {parent_interface=}."
                )

                parent_interfaces.append(parent_interface)

            interface = Interface(base=cls, inheritances=parent_interfaces)

            cls.interface = interface
        else:
            assert isinstance(cls, ConcreteClass)
            cls.interface = None


class _PropertyOfClass:
    """Represent the property with its corresponding class."""

    def __init__(self, prop: Property, cls: Class):
        """Initialize with the given values."""
        self.prop = prop
        self.cls = cls


class _ContractChecker(parse_tree.Visitor):
    """
    Verify that the contracts are well-formed.

    For example, check that the calls to verification functions are valid.
    """

    #: Symbol table to be used for de-referencing symbols, functions *etc.*
    symbol_table: Final[SymbolTable]

    #: Errors observed during the verification
    errors: List[Error]

    def __init__(self, symbol_table: SymbolTable):
        """Initialize with the given values."""
        self.symbol_table = symbol_table

        self.errors = []

    def visit_function_call(self, node: parse_tree.FunctionCall) -> None:
        verification_function = self.symbol_table.verification_functions_by_name.get(
            node.name.identifier, None
        )

        if verification_function is not None:
            # BEFORE-RELEASE (mristin, 2021-12-19):
            #  test failure case
            expected_argument_count = len(verification_function.arguments)
        elif node.name.identifier == "len":
            # BEFORE-RELEASE (mristin, 2021-12-19):
            #  test failure case
            expected_argument_count = 1
        else:
            # BEFORE-RELEASE (mristin, 2021-12-19): test this
            self.errors.append(
                Error(
                    node.original_node,
                    f"The handling of the function is not implemented: {node.name!r}",
                )
            )
            return

        if len(node.args) != expected_argument_count:
            # BEFORE-RELEASE (mristin, 2021-12-19): test this
            self.errors.append(
                Error(
                    node.original_node,
                    f"Expected exactly {expected_argument_count} arguments "
                    f"to a function call to {node.name!r}, but got: {len(node.args)}",
                )
            )

        for arg in node.args:
            self.visit(arg)


def _check_all_non_optional_properties_initialized(cls: Class) -> List[Error]:
    """
    Check that all properties of the class are properly initialized in the constructor.

    For example, check that there is a default value assigned if the constructor
    argument is optional.
    """
    errors = []  # type: List[Error]

    prop_initialized = {prop.name: False for prop in cls.properties}

    for stmt in cls.constructor.statements:
        # NOTE (mristin, 2021-12-19):
        # Check for type here since it is very likely that we introduce more statement
        # types in the future. This assertion should warn us in that case.
        assert isinstance(stmt, construction.AssignArgument)

        prop = cls.properties_by_name.get(stmt.name, None)
        assert prop is not None, "This should have been caught before: {stmt.name=}"

        if isinstance(prop.type_annotation, OptionalTypeAnnotation):
            # Since the property is optional, it is enough that we assigned it to
            # *something*, be it a ``None`` or something else.
            prop_initialized[prop.name] = True

        else:
            # The property is mandatory.

            constructor_arg = cls.constructor.arguments_by_name.get(stmt.argument, None)
            assert (
                constructor_arg is not None
            ), f"This should have been caught before. {stmt.argument=}"

            if not isinstance(constructor_arg.type_annotation, OptionalTypeAnnotation):
                # We know that the property is properly initialized since
                # the constructor argument is not optional.
                prop_initialized[prop.name] = True

            elif stmt.default is not None:
                if isinstance(
                    stmt.default,
                    (construction.EmptyList, construction.DefaultEnumLiteral),
                ):
                    # The property is mandatory, but a non-None default value is given
                    # in the assign statement so we know that the property is properly
                    # initialized.
                    prop_initialized[prop.name] = True
                else:
                    assert_never(stmt.default)
            else:
                # The property remains improperly initialized since the default value
                # has not been indicated, the property is not optional and
                # the constructor argument is optional.
                pass

    for prop_name, is_initialized in prop_initialized.items():
        if not is_initialized:
            errors.append(
                Error(
                    cls.properties_by_name[prop_name].parsed.node,
                    f"The property {prop_name!r} is not properly initialized "
                    f"in the constructor of the class {cls.name!r}.",
                )
            )

    return errors


def _over_signature_likes(symbol_table: SymbolTable) -> Iterator[SignatureLike]:
    """
    Iterate over all signature-like instances in the symbol table.

    Since interfaces are constructed on top of abstract classes and concrete classes
    with descendants, we do not iterate here over the signatures in the interfaces.
    """
    yield from symbol_table.verification_functions

    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            pass
        elif isinstance(symbol, ConstrainedPrimitive):
            pass
        elif isinstance(symbol, Class):
            yield from symbol.methods

            yield symbol.constructor

            # We do not recurse here into signatures of interfaces since they are based
            # on the methods of the corresponding class.
        else:
            assert_never(symbol)


def _verify(symbol_table: SymbolTable, ontology: _hierarchy.Ontology) -> List[Error]:
    """Perform a battery of checks on the consistency of ``symbol_table``."""
    errors = []  # type: List[Error]

    # region Check ``with_model_type`` for classes with at least one concrete descendant

    classes_in_properties = collect_ids_of_classes_in_properties(
        symbol_table=symbol_table
    )

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        if id(symbol) in classes_in_properties:
            if len(symbol.concrete_descendants) >= 1:
                if not symbol.serialization.with_model_type:
                    descendants_str = ", ".join(
                        repr(descendant.name)
                        for descendant in symbol.concrete_descendants
                    )

                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The class {symbol.name!r} has one or more concrete "
                            f"descendants ({descendants_str}), but its serialization "
                            f"setting ``with_model_type`` has not been set. We need "
                            f"to discriminate on model type at the de-serialization.",
                        )
                    )

                for descendant in symbol.concrete_descendants:
                    if not descendant.serialization.with_model_type:
                        errors.append(
                            Error(
                                descendant.parsed.node,
                                f"The class {descendant.name!r} needs to have "
                                f"serialization setting ``with_model_type`` set since "
                                f"it is among the concrete descendant classes of "
                                f"the class {symbol.name!r}. We need to discriminate "
                                f"on model type at the de-serialization",
                            )
                        )

    # endregion

    # region Check that all the function calls in the contracts are valid

    contract_checker = _ContractChecker(symbol_table=symbol_table)

    for signature_like in _over_signature_likes(symbol_table):
        for contract_or_snapshot in itertools.chain(
            signature_like.contracts.preconditions,
            signature_like.contracts.postconditions,
            signature_like.contracts.snapshots,
        ):
            assert isinstance(contract_or_snapshot, (Contract, Snapshot))
            contract_checker.visit(contract_or_snapshot.body)

    for symbol in symbol_table.symbols:
        if isinstance(symbol, Class):
            for invariant in symbol.invariants:
                contract_checker.visit(invariant.body)

    # endregion

    # region Check that all non-optional properties are initialized in the constructor

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        errors.extend(_check_all_non_optional_properties_initialized(cls=symbol))

    # endregion

    # region Check that all argument references are valid

    for signature_like in _over_signature_likes(symbol_table):
        if signature_like.description is not None:
            for arg_ref_in_doc in signature_like.description.document.findall(
                condition=doc.ArgumentReference
            ):
                assert isinstance(arg_ref_in_doc.reference, str)
                arg_name = arg_ref_in_doc.reference

                if arg_name not in signature_like.arguments_by_name:
                    errors.append(
                        Error(
                            signature_like.description.node,
                            f"The argument referenced in the docstring "
                            f"is not an argument "
                            f"of {signature_like.name!r}: {arg_name!r}",
                        )
                    )

    # endregion

    # region Assert that interfaces defined correctly

    # NOTE (mristin, 2021-12-15):
    # We expect the interfaces of the classes to be defined only for abstract classes
    # and for the concrete classes with at least one descendant.

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        if (
            isinstance(symbol, AbstractClass)
            or len(ontology.list_descendants(symbol.parsed)) > 0
        ):
            assert isinstance(symbol.interface, Interface)
        else:
            assert symbol.interface is None

    # endregion

    # region Assert that all class inheritances defined an interface

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        for inheritance in symbol.inheritances:
            assert isinstance(inheritance.interface, Interface), (
                f"Since the class {symbol.name!r} inherits from {inheritance.name!r}, "
                f"we expect that the class {inheritance.name!r} also has an interface "
                f"defined for it, but it does not."
            )

    # endregion

    return errors


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
            underlying=underlying_errors,
        )

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
        parsed_symbol_table=parsed_symbol_table, atok=atok
    )

    if constructor_error is not None:
        underlying_errors.append(constructor_error)

    # endregion

    # region Resolve settings for the JSON serialization

    serializations, serializations_error = _resolve_serializations(
        ontology=ontology, parsed_symbol_table=parsed_symbol_table
    )

    if serializations_error is not None:
        underlying_errors.append(serializations_error)

    # endregion

    if len(underlying_errors) > 0:
        # We can not proceed and recover from these errors as they concern critical
        # dependencies of the further analysis.
        return None, bundle_underlying_errors()

    # region In-line constructors

    assert constructor_table is not None

    in_lined_constructors = _in_line_constructors(
        parsed_symbol_table=parsed_symbol_table,
        ontology=ontology,
        constructor_table=constructor_table,
    )

    # endregion

    # region Figure out the sub-hierarchy of the constrained primitive types

    (
        constrained_primitives_by_name,
        determination_errors,
    ) = _determine_constrained_primitives_by_name(
        parsed_symbol_table=parsed_symbol_table, ontology=ontology
    )

    if determination_errors is not None:
        underlying_errors.extend(determination_errors)

    if len(underlying_errors) > 0:
        # We can not proceed and recover from these errors as they concern critical
        # dependencies of the further analysis.
        return None, bundle_underlying_errors()

    assert constrained_primitives_by_name is not None

    # endregion

    invariants_map = _stack_invariants(ontology=ontology)

    # region First pass of translation

    assert serializations is not None

    # Type annotations reference symbol placeholders at this point.

    symbols = []  # type: List[Symbol]
    for parsed_symbol in parsed_symbol_table.symbols:
        symbol = None  # type: Optional[Symbol]

        constrainee = constrained_primitives_by_name.get(parsed_symbol.name, None)

        if constrainee is not None:
            assert isinstance(
                parsed_symbol, parse.ConcreteClass
            ), "All constrained primitive types must be concrete."

            symbol = _parsed_class_to_constrained_primitive(
                parsed=parsed_symbol,
                constrainee=constrainee,
                invariants=invariants_map[parsed_symbol.name],
            )

        elif isinstance(parsed_symbol, parse.Enumeration):
            symbol = _parsed_enumeration_to_enumeration(parsed=parsed_symbol)

        elif isinstance(parsed_symbol, parse.Class):
            symbol = _parsed_class_to_class(
                parsed=parsed_symbol,
                ontology=ontology,
                serializations=serializations,
                invariants=invariants_map[parsed_symbol.name],
                in_lined_constructors=in_lined_constructors,
            )

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
        None,
    )

    if ref_association is None:
        raise AssertionError(
            f"The symbol associated with the references has been found in "
            f"the symbol table at the parse stage, "
            f"{parsed_symbol_table.ref_association.name=}, but could not be found "
            f"in the intermediate list of symbols."
        )

    # Check that ref association is associated with a class
    if isinstance(ref_association, Class):
        pass
    else:
        human_readable_type = None  # type: Optional[str]
        if isinstance(ref_association, Enumeration):
            human_readable_type = "enumeration"
        elif isinstance(ref_association, ConstrainedPrimitive):
            human_readable_type = "constrained primitive"
        else:
            assert_never(ref_association)

        underlying_errors.append(
            Error(
                ref_association.parsed.node,
                f"Expected the ``Ref[.]`` to be associated with a class, "
                f"but it was associated with a {human_readable_type}.",
            )
        )

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    assert isinstance(ref_association, Class), "Ref[.] associated with a class"

    meta_model = MetaModel(
        book_url=parsed_symbol_table.meta_model.book_url,
        book_version=parsed_symbol_table.meta_model.book_version,
        description=(
            _parsed_description_to_description(
                parsed_symbol_table.meta_model.description
            )
            if parsed_symbol_table.meta_model.description is not None
            else None
        ),
    )

    verification_functions = []  # type: List[VerificationUnion]
    for func in parsed_symbol_table.verification_functions:
        verification, error = _parsed_verification_function_to_verification_function(
            func
        )

        if error is not None:
            underlying_errors.append(error)
            continue

        assert verification is not None
        verification_functions.append(verification)

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    symbol_table = SymbolTable(
        symbols=symbols,
        verification_functions=verification_functions,
        ref_association=ref_association,
        meta_model=meta_model,
    )

    # endregion

    # NOTE (mristin, 2021-12-14):
    # At first we in-lined all these second-pass code. However, since Python keeps
    # all the variables in the function scope, the code became quite unreadable and
    # we were never sure which variables are re-used between the passes.
    #
    # Hence we refactored the second passes in the separate functions. Please keep the
    # order of the functions with their call order here, and do not call them elsewhere
    # in code.

    underlying_errors.extend(
        _second_pass_to_resolve_symbols_in_atomic_types_in_place(
            symbol_table=symbol_table
        )
    )

    underlying_errors.extend(
        _second_pass_to_resolve_symbol_references_in_the_descriptions_in_place(
            symbol_table=symbol_table
        )
    )

    underlying_errors.extend(
        _second_pass_to_resolve_attribute_references_in_the_descriptions_in_place(
            symbol_table=symbol_table
        )
    )

    underlying_errors.extend(
        _second_pass_to_resolve_default_argument_values_in_place(
            symbol_table=symbol_table
        )
    )

    underlying_errors.extend(
        _second_pass_to_resolve_supersets_of_enumerations_in_place(
            symbol_table=symbol_table
        )
    )

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, (ConstrainedPrimitive, Class)):
            continue

    _second_pass_to_resolve_inheritances_in_place(symbol_table=symbol_table)

    _second_pass_to_resolve_resulting_class_of_specified_for(
        symbol_table=symbol_table,
    )

    _second_pass_to_resolve_specified_for_in_invariants(
        symbol_table=symbol_table,
    )

    _second_pass_to_resolve_descendants_in_place(
        symbol_table=symbol_table, ontology=ontology
    )

    _second_pass_to_resolve_interfaces_in_place(
        symbol_table=symbol_table, ontology=ontology
    )

    underlying_errors.extend(_verify(symbol_table=symbol_table, ontology=ontology))

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    return symbol_table, None


def errors_if_contracts_for_functions_or_methods_defined(
    symbol_table: SymbolTable,
) -> Optional[List[Error]]:
    """
    Generate an error if one or more contracts for functions or methods defined.

    We added some support for the pre-conditions, post-conditions and snapshots
    already and keep maintaining it as it is only a matter of time when we will
    introduce their transpilation. Introducing them "after the fact" would have been
    much more difficult.

    At the given moment, however, we deliberately focus only on the invariants.
    """
    errors = []  # type: List[Error]
    for signature_like in _over_signature_likes(symbol_table):
        if (
            len(signature_like.contracts.preconditions) > 0
            or len(signature_like.contracts.postconditions) > 0
            or len(signature_like.contracts.snapshots) > 0
        ):
            original_node = None  # type: Optional[ast.AST]

            if signature_like.parsed is not None:
                original_node = signature_like.parsed.node

            errors.append(
                Error(
                    original_node,
                    f"Pre-condition, snapshot or post-condition defined "
                    f"for {signature_like.name!r}",
                )
            )

    if len(errors) > 0:
        return errors

    return None


def errors_if_non_implementation_specific_methods(
    symbol_table: SymbolTable,
) -> Optional[List[Error]]:
    """
    Generate an error if one or more class methods are not implementation-specific.

    We added some support for understood methods already and keep maintaining it as
    it is only a matter of time when we will introduce their transpilation. Introducing
    them "after the fact" would have been much more difficult.

    At the given moment, however, we deliberately focus only on implementation-specific
    methods.
    """
    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        for method in symbol.methods:
            if not isinstance(method, ImplementationSpecificMethod):
                errors.append(
                    Error(
                        method.parsed.node,
                        f"Method {method.name!r} of class {symbol.name!r} is not "
                        f"implementation-specific",
                    )
                )

    if len(errors) > 0:
        return errors

    return None
