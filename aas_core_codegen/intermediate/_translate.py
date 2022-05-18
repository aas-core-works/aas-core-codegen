"""Translate the parsed representation into the intermediate representation."""
import ast
import collections
import itertools
import re
from typing import (
    Sequence,
    List,
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
    Set,
    Dict,
    OrderedDict,
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
    rendering,
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
    Class,
    Constructor,
    Symbol,
    ListTypeAnnotation,
    OptionalTypeAnnotation,
    OurTypeAnnotation,
    STR_TO_PRIMITIVE_TYPE,
    PrimitiveTypeAnnotation,
    DefaultEnumerationLiteral,
    MetaModel,
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
    collect_ids_of_symbols_in_properties,
    SymbolExceptEnumeration,
    ReferenceInTheBook,
    SignatureDescription,
    MetaModelDescription,
    SymbolDescription,
    PropertyDescription,
    EnumerationLiteralDescription,
    DescriptionUnion,
    find_first_field_list,
    SummaryRemarksConstraintsDescription,
    MethodUnion,
    beneath_optional,
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

    def __repr__(self) -> str:
        return f"{_PlaceholderAttributeReference.__name__}(path={self.path!r})"


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


# noinspection PyUnusedLocal
def _constraint_reference_role(  # type: ignore
    role, rawtext, text, lineno, inliner, options=None, content=None
) -> Any:
    """Create a reference in the documentation to a constraint."""
    # See: https://docutils.sourceforge.io/docs/howto/rst-roles.html
    if content is None:
        content = []

    if options is None:
        options = {}

    docutils.parsers.rst.roles.set_classes(options)

    reference = text

    node = doc.ConstraintReference(
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
docutils.parsers.rst.roles.register_local_role(
    "constraintref", _constraint_reference_role
)


# region Descriptions


class _StructuredDescription:
    """Represent a structured description extracted from a docstring."""

    # fmt: off
    @require(
        lambda summary:
        find_first_field_list(summary) is None,
        "Summary expected without field lists"
    )
    @require(
        lambda remarks:
        all(
            find_first_field_list(remark) is None
            for remark in remarks
        ),
        "Remarks expected without field lists"
    )
    @require(
        lambda fields_by_name:
        all(
            find_first_field_list(body) is None
            for body in fields_by_name.values()
        ),
        "Field bodies expected without sub-field lists"
    )
    # fmt: on
    def __init__(
        self,
        summary: docutils.nodes.paragraph,
        remarks: List[docutils.nodes.Element],
        fields_by_name: OrderedDict[str, docutils.nodes.field_body],
    ) -> None:
        """Initialize with the given values."""
        self.summary = summary
        self.remarks = remarks
        self.fields_by_name = fields_by_name


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _extract_structured_description(
    parsed: parse.Description,
) -> Tuple[Optional[_StructuredDescription], Optional[List[Error]]]:
    """Extract structured information from a description."""
    if len(parsed.document.children) == 0:
        return None, [Error(parsed.node, "Unexpected empty description")]

    cursor = iter(parsed.document.children)
    lookahead = next(cursor, None)

    errors = []  # type: List[Error]

    if not isinstance(lookahead, docutils.nodes.paragraph):
        errors.append(
            Error(
                parsed.node,
                f"Expected the first document element to be a summary and "
                f"thus a paragraph, but got: {lookahead}",
            )
        )

    # region Match

    summary = lookahead
    remarks = []  # type: List[docutils.nodes.Element]
    field_list = None  # type: Optional[docutils.nodes.field_list]

    lookahead = next(cursor, None)
    while lookahead is not None:
        if isinstance(lookahead, docutils.nodes.field_list):
            field_list = lookahead
        else:
            assert lookahead is not None
            remarks.append(lookahead)

        lookahead = next(cursor, None)

    if field_list is not None and lookahead is not None:
        errors.append(
            Error(
                parsed.node,
                f"Expected no document elements after the field list, "
                f"but got: {lookahead}",
            )
        )

    # endregion

    # region Check summary and remarks

    assert summary is not None

    field_list_in_summary = next(summary.findall(docutils.nodes.field_list), None)
    if field_list_in_summary is not None:
        errors.append(
            Error(
                parsed.node,
                f"Expected no field lists in the summary, "
                f"but the summary contains one: {field_list_in_summary}",
            )
        )

    for i, remark in enumerate(remarks):
        field_list_in_remark = next(remark.findall(docutils.nodes.field_list), None)
        if field_list_in_remark is not None:
            errors.append(
                Error(
                    parsed.node,
                    f"Expected no field lists in remarks, "
                    f"but the remark {i + 1} contains one: {field_list_in_remark}",
                )
            )

    # endregion

    # region Transform the field list to an ordered dictionary

    fields_by_name = (
        collections.OrderedDict()
    )  # type: OrderedDict[str, docutils.nodes.field_body]

    if field_list is not None:
        for field in field_list.children:
            if len(field.children) != 2:
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected exactly two document elements in a field, "
                        f"but got {len(field.children)}: {field}",
                    )
                )
                continue

            field_name, field_body = field.children
            if not isinstance(field_name, docutils.nodes.field_name):
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected the field name to be a ``field_name``, "
                        f"but got {type(field_name)} : {field_name}",
                    )
                )
                continue
            if not isinstance(field_body, docutils.nodes.field_body):
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected the field body to be a ``field_body``, "
                        f"but got {type(field_body)} : {field_body}",
                    )
                )
                continue

            assert isinstance(field_name, docutils.nodes.field_name)
            assert isinstance(field_body, docutils.nodes.field_body)

            if len(field_name.children) != 1:
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected exactly one sub-element in the field name, "
                        f"but got {len(field_name.children)} : {field_name}",
                    )
                )
                continue

            if not isinstance(field_name.children[0], docutils.nodes.Text):
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected the field name to be text, "
                        f"but got {type(field_name.children[0])} : {field_name}",
                    )
                )
                continue

            name = field_name.children[0].astext()

            field_list_in_body = next(
                field_body.findall(condition=docutils.nodes.field_list), None
            )

            if field_list_in_body is not None:
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected no nested field lists, "
                        f"but got a field list nested "
                        f"under the field {name} : {field_list_in_body}",
                    )
                )
                continue

            fields_by_name[name] = field_body

    # endregion

    if len(errors) > 0:
        return None, errors

    return (
        _StructuredDescription(
            summary=summary, remarks=remarks, fields_by_name=fields_by_name
        ),
        None,
    )


_SummaryRemarksConstraintsDescriptionT = TypeVar(
    "_SummaryRemarksConstraintsDescriptionT", bound=SummaryRemarksConstraintsDescription
)


def _to_summary_remarks_constraints_description(
    parsed: parse.Description, factory: Type[_SummaryRemarksConstraintsDescriptionT]
) -> Tuple[Optional[_SummaryRemarksConstraintsDescriptionT], Optional[List[Error]]]:
    """Translate the description and produce the instance using the ``factory``."""
    structured_desc, structured_desc_errors = _extract_structured_description(
        parsed=parsed
    )
    if structured_desc_errors is not None:
        return None, structured_desc_errors

    assert structured_desc is not None

    errors = []  # type: List[Error]

    constraints_by_identifier = (
        collections.OrderedDict()
    )  # type: OrderedDict[str, docutils.nodes.field_body]

    for name, body in structured_desc.fields_by_name.items():
        parts = name.split()
        if len(parts) != 2:
            errors.append(
                Error(
                    parsed.node,
                    f"Expected only directives such as "
                    f"``constraint some-identifier`` "
                    f"in this context, but got a directive with {len(parts)} part(s): "
                    f"{name}",
                )
            )
            continue

        if parts[0].lower() != "constraint":
            errors.append(
                Error(
                    parsed.node,
                    f"Expected only directives such as "
                    f"``constraint some-identifier`` "
                    f"in this context, but got a directive with "
                    f"the first part {parts[0]!r}: {name}",
                )
            )
            continue

        constraint_id = parts[1]

        if constraint_id in constraints_by_identifier:
            errors.append(
                Error(
                    parsed.node,
                    f"Expected all constraints to have unique identifiers, "
                    f"but two or more constraints share the identifier: {constraint_id}",
                )
            )

        constraints_by_identifier[constraint_id] = body

    if len(errors) > 0:
        return None, errors

    return (
        factory(
            summary=structured_desc.summary,
            remarks=structured_desc.remarks,
            constraints_by_identifier=constraints_by_identifier,
            parsed=parsed,
        ),
        None,
    )


def _to_meta_model_description(
    parsed: parse.Description,
) -> Tuple[Optional[MetaModelDescription], Optional[List[Error]]]:
    """Structure the information from the docstring of the meta-model."""
    return _to_summary_remarks_constraints_description(
        parsed=parsed, factory=MetaModelDescription
    )


def _to_symbol_description(
    parsed: parse.Description,
) -> Tuple[Optional[SymbolDescription], Optional[List[Error]]]:
    """Structure the information from the docstring of a symbol."""
    return _to_summary_remarks_constraints_description(
        parsed=parsed, factory=SymbolDescription
    )


def _to_property_description(
    parsed: parse.Description,
) -> Tuple[Optional[PropertyDescription], Optional[List[Error]]]:
    """Translate the description into a structured property description."""
    return _to_summary_remarks_constraints_description(
        parsed=parsed, factory=PropertyDescription
    )


def _to_enumeration_literal_description(
    parsed: parse.Description,
) -> Tuple[Optional[EnumerationLiteralDescription], Optional[List[Error]]]:
    """Translate ``parsed`` into a structured description of an enumeration literal."""
    structured_desc, structured_desc_errors = _extract_structured_description(
        parsed=parsed
    )
    if structured_desc_errors is not None:
        return None, structured_desc_errors
    assert structured_desc is not None

    field_list = next(parsed.document.findall(docutils.nodes.field_list), None)
    if field_list is not None:
        return None, [
            Error(
                parsed.node,
                f"Expected no field list in a description of an enumeration literal, "
                f"but got at least one: {field_list}",
            )
        ]

    assert (
        len(structured_desc.fields_by_name) == 0
    ), "Expected to match the previous findall"

    return (
        EnumerationLiteralDescription(
            summary=structured_desc.summary,
            remarks=structured_desc.remarks,
            parsed=parsed,
        ),
        None,
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _to_signature_description(
    parsed: parse.Description,
    arguments: Sequence["Argument"],
    returns: Optional[TypeAnnotationUnion],
) -> Tuple[Optional[SignatureDescription], Optional[List[Error]]]:
    """Translate ``parsed`` into a structured description of a signature."""
    structured_desc, structured_desc_errors = _extract_structured_description(
        parsed=parsed
    )
    if structured_desc_errors is not None:
        return None, structured_desc_errors
    assert structured_desc is not None

    errors = []  # type: List[Error]

    argument_descriptions_by_name = (
        collections.OrderedDict()
    )  # type: OrderedDict[Identifier, docutils.nodes.field_body]

    returns_description = None  # type: Optional[docutils.nodes.field_body]

    for name, body in structured_desc.fields_by_name.items():
        parts = name.split()
        if len(parts) > 2:
            errors.append(
                Error(
                    parsed.node, f"Unexpected field name with more than 2 parts: {name}"
                )
            )
            continue

        directive = parts[0]
        if directive.lower() == "param":
            arg_name = parts[1]
            if not IDENTIFIER_RE.fullmatch(arg_name):
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected the argument name to be a valid identifier, "
                        f"but got: {arg_name}",
                    )
                )
                continue

            if arg_name in argument_descriptions_by_name:
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected non-duplicate argument descriptions, "
                        f"but got two or more for the argument {arg_name!r}",
                    )
                )
                continue

            argument_descriptions_by_name[Identifier(arg_name)] = body

        elif directive.lower() in ("return", "returns"):
            if len(parts) > 1:
                errors.append(
                    Error(
                        parsed.node,
                        f"Expected return field without additional parts, "
                        f"but got: {parts[1:]}",
                    )
                )
                continue

            if returns_description is not None:
                errors.append(
                    Error(
                        parsed.node,
                        "Expected a single ``return`` field, but got two or more",
                    )
                )
                continue

            returns_description = body
        else:
            errors.append(Error(parsed.node, f"Unexpected field: {name}"))
            continue

    if returns is None and returns_description is not None:
        errors.append(
            Error(
                parsed.node,
                f"No return value is specified, "
                f"but the return value is in the description: {returns_description}",
            )
        )

    arg_name_set = {arg.name for arg in arguments}
    for arg_name, arg_description in argument_descriptions_by_name.items():
        if arg_name not in arg_name_set:
            errors.append(
                Error(
                    parsed.node,
                    f"The argument {arg_name} has not been specified, "
                    f"but is listed in the description: {arg_description}",
                )
            )

    description = SignatureDescription(
        summary=structured_desc.summary,
        remarks=structured_desc.remarks,
        arguments_by_name=argument_descriptions_by_name,
        returns=returns_description,
        parsed=parsed,
    )

    for arg_ref_in_doc in _find_all_in_signature_description(
        element_type=doc.ArgumentReference, signature_description=description
    ):
        assert isinstance(arg_ref_in_doc.reference, str)

        arg_name = arg_ref_in_doc.reference
        if arg_name not in arg_name_set:
            errors.append(
                Error(
                    parsed.node,
                    f"The argument referenced in the description "
                    f"is not listed as an argument: {arg_name!r}",
                )
            )

    if len(errors) > 0:
        return None, errors

    return description, None


# endregion


class _PlaceholderSymbol:
    """Reference something which will be resolved once the table is built."""

    def __init__(self, name: str) -> None:
        """Initialize with the given values."""
        self.name = name

    def __repr__(self) -> str:
        return f"{_PlaceholderSymbol.__name__}(name={self.name!r})"


def _propagate_parsed_reference_in_the_book(
    parsed: parse.ReferenceInTheBook,
) -> ReferenceInTheBook:
    """Decouple the parsed reference in the book to the intermediate level."""
    return ReferenceInTheBook(
        section=parsed.section,
        index=parsed.index,
        fragment=parsed.fragment,
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _to_enumeration_literal(
    parsed: parse.EnumerationLiteral,
) -> Tuple[Optional[EnumerationLiteral], Optional[List[Error]]]:
    """Translate the enumeration literal from the meta-model."""
    description = None  # type: Optional[EnumerationLiteralDescription]

    if parsed.description is not None:
        description, description_errors = _to_enumeration_literal_description(
            parsed.description
        )
        if description_errors is not None:
            return None, description_errors

    return (
        EnumerationLiteral(
            name=parsed.name,
            value=parsed.value,
            description=description,
            parsed=parsed,
        ),
        None,
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _to_enumeration(
    parsed: parse.Enumeration,
) -> Tuple[Optional[Enumeration], Optional[List[Error]]]:
    """Translate an enumeration from the meta-model to an intermediate enumeration."""
    errors = []  # type: List[Error]

    description = None  # type: Optional[SymbolDescription]
    if parsed.description is not None:
        description, description_errors = _to_symbol_description(parsed.description)
        if description_errors is not None:
            errors.extend(description_errors)

    literals = []  # type: List[EnumerationLiteral]
    for parsed_literal in parsed.literals:
        literal, literal_errors = _to_enumeration_literal(parsed_literal)
        if literal_errors is not None:
            errors.append(
                Error(
                    parsed_literal.node,
                    f"Failed to parse the enumeration literal {parsed_literal.name!r}",
                    literal_errors,
                )
            )
            continue

        assert literal is not None
        literals.append(literal)

    if len(errors) > 0:
        return None, errors

    return (
        Enumeration(
            name=parsed.name,
            literals=literals,
            # NOTE (mristin, 2021-12-27):
            # Postpone the resolution to the second pass once the symbol table has been
            # completely built
            is_superset_of=cast(
                List[Enumeration],
                [
                    _PlaceholderSymbol(name=identifier)
                    for identifier in parsed.is_superset_of
                ],
            ),
            reference_in_the_book=_propagate_parsed_reference_in_the_book(
                parsed.reference_in_the_book
            )
            if parsed.reference_in_the_book is not None
            else None,
            description=description,
            parsed=parsed,
        ),
        None,
    )


def _to_type_annotation(
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
                items=_to_type_annotation(parsed.subscripts[0]),
                parsed=parsed,
            )

        elif parsed.identifier == "Optional":
            assert len(parsed.subscripts) == 1, (
                f"Expected exactly one subscript for the Optional type annotation, "
                f"but got: {parsed}; this should have been caught before!"
            )

            return OptionalTypeAnnotation(
                value=_to_type_annotation(parsed.subscripts[0]),
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


def _to_arguments(parsed: Sequence[parse.Argument]) -> List[Argument]:
    """Translate the arguments of a method in meta-model to the intermediate ones."""
    return [
        Argument(
            name=parsed_arg.name,
            type_annotation=_to_type_annotation(parsed_arg.type_annotation),
            default=_DefaultPlaceholder(parsed=parsed_arg.default)  # type: ignore
            if parsed_arg.default is not None
            else None,
            parsed=parsed_arg,
        )
        for parsed_arg in parsed
        if not isinstance(parsed_arg.type_annotation, parse.SelfTypeAnnotation)
    ]


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _to_property(
    parsed: parse.Property, parsed_cls: parse.Class
) -> Tuple[Optional[Property], Optional[List[Error]]]:
    """Translate a parsed property of a class to an intermediate one."""
    description = None  # type: Optional[PropertyDescription]

    if parsed.description is not None:
        description, description_errors = _to_property_description(parsed.description)
        if description_errors is not None:
            return None, description_errors

    # noinspection PyTypeChecker
    return (
        Property(
            name=parsed.name,
            type_annotation=_to_type_annotation(parsed.type_annotation),
            description=description,
            # NOTE (mristin, 2021-12-26):
            # We can only resolve the ``specified_for`` when the class is actually
            # created. Therefore, we assign here a placeholder and fix it later in a second
            # pass.
            specified_for=_PlaceholderSymbol(parsed_cls.name),  # type: ignore
            parsed=parsed,
        ),
        None,
    )


def _to_contracts(parsed: parse.Contracts) -> Contracts:
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
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _to_method(
        parsed: Union[parse.UnderstoodMethod, parse.ImplementationSpecificMethod],
        parsed_cls: parse.Class
) -> Tuple[
    Optional[Union[UnderstoodMethod, ImplementationSpecificMethod]],
    Optional[List[Error]]
]:
    """Translate the parsed method into an intermediate representation."""
    arguments = _to_arguments(parsed=parsed.arguments)

    returns = (
        None
        if parsed.returns is None
        else _to_type_annotation(parsed.returns)
    )

    # fmt: on
    description = None  # type: Optional[SignatureDescription]
    if parsed.description:
        description, description_errors = _to_signature_description(
            parsed=parsed.description,
            arguments=arguments,
            returns=returns
        )
        if description_errors is not None:
            return None, description_errors

    # NOTE (mristin, 2021-12-26):
    # We can only resolve the ``specified_for`` when the class is actually
    # created. Therefore, we assign here a placeholder and fix it later in a second
    # pass.
    specified_for_placeholder = _PlaceholderSymbol(parsed_cls.name)

    contracts = _to_contracts(parsed.contracts)

    if isinstance(parsed, parse.ImplementationSpecificMethod):
        # noinspection PyTypeChecker
        return ImplementationSpecificMethod(
            name=parsed.name,
            arguments=arguments,
            returns=returns,
            description=description,
            specified_for=specified_for_placeholder,  # type: ignore
            contracts=contracts,
            parsed=parsed,
        ), None
    elif isinstance(parsed, parse.UnderstoodMethod):
        # noinspection PyTypeChecker
        return UnderstoodMethod(
            name=parsed.name,
            arguments=arguments,
            returns=returns,
            description=description,
            specified_for=specified_for_placeholder,  # type: ignore
            contracts=contracts,
            body=parsed.body,
            parsed=parsed,
        ), None
    else:
        assert_never(parsed)

    raise AssertionError("Should have never gotten here")


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
    # NOTE (mristin, 2022-03-18):
    # While we perform different stackings in second passes, we can not stack the
    # constrainees in the second pass since we need to determine whether a class is a
    # constrained primitive *or* an abstract or a concrete class.

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


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _to_constrained_primitive(
    parsed: parse.ConcreteClass, constrainee: PrimitiveType
) -> Tuple[Optional[ConstrainedPrimitive], Optional[List[Error]]]:
    """
    Translate a concrete class to a constrained primitive.

    The ``parsed`` is expected to be tested for being a valid constrained primitive
    before calling this function.

    The ``constrainee`` is determined by propagation in
    :py:function:`_determine_constrained_primitives_by_name`.
    """
    # noinspection PyTypeChecker
    invariants = [
        Invariant(
            description=parsed_invariant.description,
            body=parsed_invariant.body,
            specified_for=_PlaceholderSymbol(parsed.name),  # type: ignore
            parsed=parsed_invariant,
        )
        for parsed_invariant in parsed.invariants
    ]

    description = None  # type: Optional[SymbolDescription]

    if parsed.description is not None:
        description, description_errors = _to_symbol_description(parsed.description)
        if description_errors is not None:
            return None, description_errors

    # noinspection PyTypeChecker
    return (
        ConstrainedPrimitive(
            name=parsed.name,
            # Use placeholders for inheritances and descendants as we are still in
            # the first pass and building up the symbol table. They will be resolved in
            # a second pass.
            inheritances=[],
            descendants=[],
            constrainee=constrainee,
            is_implementation_specific=parsed.is_implementation_specific,
            invariants=invariants,
            reference_in_the_book=_propagate_parsed_reference_in_the_book(
                parsed.reference_in_the_book
            )
            if parsed.reference_in_the_book is not None
            else None,
            description=description,
            parsed=parsed,
        ),
        None,
    )


class _MaybeInterfacePlaceholder:
    """
    Represent a placeholder for the interfaces.

    We do not know in the first pass whether a class will have an interface defined
    or not.
    """


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _extract_constructor(
    parsed_class: parse.ClassUnion,
    constructor_statements: Sequence[construction.Statement],
) -> Tuple[Optional[Constructor], Optional[List[Error]]]:
    """
    Extract the constructor from the given ``parsed_class``.

    The ``constructor_statements`` are determined by the constructor table. The calls
    to super-constructors are not expected to be in-lined yet.
    """
    contracts = Contracts(preconditions=[], snapshots=[], postconditions=[])
    arguments = []  # type: List[Argument]
    init_is_implementation_specific = False
    description = None  # type: Optional[SignatureDescription]

    errors = []  # type: List[Error]

    parsed_class_init = parsed_class.methods_by_name.get(Identifier("__init__"), None)
    if parsed_class_init is not None:
        arguments = _to_arguments(parsed=parsed_class_init.arguments)

        init_is_implementation_specific = isinstance(
            parsed_class_init, parse.ImplementationSpecificMethod
        )

        contracts = _to_contracts(parsed_class_init.contracts)

        if parsed_class_init.description is not None:
            (description, description_errors,) = _to_signature_description(
                parsed=parsed_class_init.description, arguments=arguments, returns=None
            )
            if description_errors is not None:
                errors.extend(description_errors)

    if len(errors) > 0:
        return None, errors

    constructor = Constructor(
        is_implementation_specific=init_is_implementation_specific,
        arguments=arguments,
        contracts=contracts,
        description=description,
        # NOTE (mristin, 2022-03-19):
        # We ignore the typing system for the moment and allow calls to
        # super constructors in the statements. In the
        # :py:func:`_second_pass_to_stack_constructors`, we will in-line them.
        statements=constructor_statements,  # type: ignore
        parsed=(parsed_class_init if parsed_class_init is not None else None),
    )

    return constructor, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _to_class(
    parsed: parse.ClassUnion, constructor_statements: Sequence[construction.Statement]
) -> Tuple[Optional[ClassUnion], Optional[List[Error]]]:
    """
    Translate a concrete parsed class to an intermediate class.

    The ``constructor_statements`` are determined by the constructor table. The calls
    to super-constructors are not expected to be in-lined yet.
    """
    serialization = None  # type: Optional[Serialization]
    if parsed.serialization is not None:
        # NOTE (mristin, 2022-03-19):
        # The ``parsed.serialization.with_model_type`` might be None, but we have to
        # allow it here as we will apply a second pass and properly inherit the
        # with_model_type.
        serialization = Serialization(
            with_model_type=parsed.serialization.with_model_type  # type: ignore
        )

    # noinspection PyTypeChecker
    invariants = [
        Invariant(
            description=parsed_invariant.description,
            body=parsed_invariant.body,
            specified_for=_PlaceholderSymbol(parsed.name),  # type: ignore
            parsed=parsed_invariant,
        )
        for parsed_invariant in parsed.invariants
    ]

    errors = []  # type: List[Error]

    properties = []  # type: List[Property]
    for parsed_prop in parsed.properties:
        prop, prop_errors = _to_property(parsed=parsed_prop, parsed_cls=parsed)
        if prop_errors is not None:
            errors.append(
                Error(
                    parsed_prop.node,
                    f"Failed to parse the property {parsed_prop.name!r}",
                    prop_errors,
                )
            )
            continue

        assert prop is not None
        properties.append(prop)

    constructor, constructor_errors = _extract_constructor(
        parsed_class=parsed, constructor_statements=constructor_statements
    )
    if constructor_errors is not None:
        errors.append(
            Error(
                parsed.node,
                f"Failed to parsed the constructor of the class {parsed.name!r}",
                constructor_errors,
            )
        )

    methods = []  # type: List[MethodUnion]
    for parsed_method in parsed.methods:
        if isinstance(parsed_method, parse.ConstructorToBeUnderstood):
            # Constructors are handled in a different way through
            # :py:class:`Constructors`.
            continue

        method, method_errors = _to_method(parsed=parsed_method, parsed_cls=parsed)
        if method_errors is not None:
            errors.append(
                Error(
                    parsed_method.node,
                    f"Failed to parse the method {parsed_method.name!r}",
                    method_errors,
                )
            )
            continue

        assert method is not None
        methods.append(method)

    description = None  # type: Optional[SymbolDescription]
    if parsed.description is not None:
        description, description_errors = _to_symbol_description(
            parsed=parsed.description
        )
        if description_errors is not None:
            errors.extend(description_errors)

    if len(errors) > 0:
        return None, errors

    assert constructor is not None

    factory_to_use = None  # type: Optional[Type[Class]]

    if isinstance(parsed, parse.ConcreteClass):
        factory_to_use = ConcreteClass
    elif isinstance(parsed, parse.AbstractClass):
        factory_to_use = AbstractClass
    else:
        assert_never(parsed)

    assert factory_to_use is not None

    # noinspection PyTypeChecker
    return (
        factory_to_use(
            name=parsed.name,
            # Use a placeholder for inheritances, descendants and the interface as we can
            # not resolve inheritances at this point
            inheritances=[],
            interface=_MaybeInterfacePlaceholder(),  # type: ignore
            descendants=[],
            is_implementation_specific=parsed.is_implementation_specific,
            properties=properties,
            methods=methods,
            constructor=constructor,
            invariants=invariants,
            # We allow temporarily the ``serialization`` to be possibly None since we
            # have to resolve it in the second pass in
            # :py:func:`_second_pass_to_stack_serializations`.
            serialization=serialization,  # type: ignore
            reference_in_the_book=_propagate_parsed_reference_in_the_book(
                parsed=parsed.reference_in_the_book
            )
            if parsed.reference_in_the_book is not None
            else None,
            description=description,
            parsed=parsed,
        ),
        None,
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
def _to_verification_function(
    parsed: parse.FunctionUnion,
) -> Tuple[Optional[VerificationUnion], Optional[List[Error]]]:
    """Translate the verification function and try to understand it, if necessary."""
    name = parsed.name
    arguments = _to_arguments(parsed=parsed.arguments)
    returns = None if parsed.returns is None else _to_type_annotation(parsed.returns)

    errors = []  # type: List[Error]

    description = None  # type: Optional[SignatureDescription]
    if parsed.description is not None:
        description, description_errors = _to_signature_description(
            parsed=parsed.description, arguments=arguments, returns=returns
        )
        if description_errors is not None:
            errors.extend(description_errors)

    contracts = _to_contracts(parsed.contracts)

    if isinstance(parsed, parse.ImplementationSpecificMethod):
        if len(errors) > 0:
            return None, errors

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
            errors.append(fatal_error)
            return None, errors

        # NOTE (mristin, 2021-01-02):
        # Since we only have a single rule, we also return an ``ok_error`` as critical
        # error to explain the user what we could not match. In the future, when
        # there are more rules, we should trace all the "ok" errors and explain why
        # *each single rule* did not match so that the user can debug their verification
        # functions.

        if ok_error is not None:
            errors.append(
                Error(
                    parsed.node,
                    f"We do not know how to interpret the verification function {name!r} "
                    f"as it does not match our pre-defined interpretation rules. "
                    f"Please contact the developers if you expect this function "
                    f"to be understood.",
                    [ok_error],
                ),
            )

        if len(errors) > 0:
            return None, errors

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
        errors.append(
            Error(parsed.node, "Unexpected constructor as a verification function")
        )
        return None, errors
    else:
        assert_never(parsed)

    raise AssertionError("Should not have gotten here")


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _to_meta_model(
    parsed: parse.MetaModel,
) -> Tuple[Optional[MetaModel], Optional[List[Error]]]:
    """Translate the meta-model meta-data."""
    description = None  # type: Optional[MetaModelDescription]
    if parsed.description is not None:
        description, description_errors = _to_meta_model_description(parsed.description)
        if description_errors is not None:
            return None, description_errors

    return (
        MetaModel(
            book_url=parsed.book_url,
            book_version=parsed.book_version,
            description=description,
        ),
        None,
    )


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


_DocElementT = TypeVar("_DocElementT", bound=docutils.nodes.Element)


def _find_all_in_symbol_description(
    element_type: Type[_DocElementT], symbol_description: SymbolDescription
) -> Iterator[_DocElementT]:
    """Iterate over all the fields of the description and yield the desired elements."""
    yield from symbol_description.summary.findall(element_type)

    for remark in symbol_description.remarks:
        yield from remark.findall(element_type)

    for constraint in symbol_description.constraints_by_identifier.values():
        yield from constraint.findall(element_type)


def _find_all_in_enumeration_literal_description(
    element_type: Type[_DocElementT],
    enumeration_literal_description: EnumerationLiteralDescription,
) -> Iterator[_DocElementT]:
    """Iterate over all the fields of the description and yield the desired elements."""
    yield from enumeration_literal_description.summary.findall(element_type)

    for remark in enumeration_literal_description.remarks:
        yield from remark.findall(element_type)


def _find_all_in_property_description(
    element_type: Type[_DocElementT], property_description: PropertyDescription
) -> Iterator[_DocElementT]:
    """Iterate over all the fields of the description and yield the desired elements."""
    yield from property_description.summary.findall(element_type)

    for remark in property_description.remarks:
        yield from remark.findall(element_type)

    for body in property_description.constraints_by_identifier.values():
        yield from body.findall(element_type)


def _find_all_in_signature_description(
    element_type: Type[_DocElementT], signature_description: SignatureDescription
) -> Iterator[_DocElementT]:
    """
    Iterate over all the fields of the description and yield the desired elements.

    We also return the description for the client to report errors etc.
    """
    yield from signature_description.summary.findall(element_type)

    for remark in signature_description.remarks:
        yield from remark.findall(element_type)

    for arg_description in signature_description.arguments_by_name.values():
        yield from arg_description.findall(element_type)

    if signature_description.returns is not None:
        yield from signature_description.returns.findall(element_type)


def _find_all_in_meta_model_description(
    element_type: Type[_DocElementT], meta_model_description: MetaModelDescription
) -> Iterator[_DocElementT]:
    """
    Iterate over all the fields of the description and yield the desired elements.

    We also return the description for the client to report errors etc.
    """
    yield from meta_model_description.summary.findall(element_type)

    for remark in meta_model_description.remarks:
        for element in remark.findall(element_type):
            yield element

    for constraint in meta_model_description.constraints_by_identifier.values():
        for element in constraint.findall(element_type):
            yield element


def _over_descriptions_and_their_symbols(
    symbol_table: SymbolTable,
) -> Iterator[Tuple[DescriptionUnion, Optional[Symbol]]]:
    """
    Iterate over the descriptions along the symbols in which they are defined.

    For some descriptions, such as the descriptions of the meta-model itself, no
    symbol exists. We yield None in those cases.
    """
    for symbol in symbol_table.symbols:
        if symbol.description is not None:
            yield symbol.description, symbol

        if isinstance(symbol, Enumeration):
            for literal in symbol.literals:
                if literal.description is not None:
                    yield literal.description, symbol

        elif isinstance(symbol, ConstrainedPrimitive):
            # No special sub-descriptions in the constrained primitive
            pass

        elif isinstance(symbol, (AbstractClass, ConcreteClass)):
            for prop in symbol.properties:
                if prop.description is not None:
                    yield prop.description, symbol

            for method in symbol.methods:
                if method.description is not None:
                    yield method.description, symbol
        else:
            assert_never(symbol)

    for verification in symbol_table.verification_functions:
        if verification.description is not None:
            yield verification.description, None

    if symbol_table.meta_model.description is not None:
        yield symbol_table.meta_model.description, None


def _find_all_in_descriptions(
    element_type: Type[_DocElementT], symbol_table: SymbolTable
) -> Iterator[Tuple[_DocElementT, DescriptionUnion, Optional[Symbol]]]:
    """
    Iterate over the descriptions and yield the desired documentation elements.

    We return the corresponding description containing the element as well as
    the outer symbol in which context the description is given.

    If there is no symbol available as a context, which is the case for example in
    verification functions, no symbol is yielded.
    """
    for description, symbol in _over_descriptions_and_their_symbols(
        symbol_table=symbol_table
    ):
        if isinstance(description, SymbolDescription):
            for element in _find_all_in_symbol_description(
                element_type=element_type, symbol_description=description
            ):
                yield element, description, symbol
        elif isinstance(description, EnumerationLiteralDescription):
            for element in _find_all_in_enumeration_literal_description(
                element_type=element_type, enumeration_literal_description=description
            ):
                yield element, description, symbol
        elif isinstance(description, PropertyDescription):
            for element in _find_all_in_property_description(
                element_type=element_type, property_description=description
            ):
                yield element, description, symbol
        elif isinstance(description, SignatureDescription):
            for element in _find_all_in_signature_description(
                element_type=element_type, signature_description=description
            ):
                yield element, description, symbol
        elif isinstance(description, MetaModelDescription):
            for element in _find_all_in_meta_model_description(
                element_type=element_type, meta_model_description=description
            ):
                yield element, description, symbol
        else:
            assert_never(description)


def _second_pass_to_resolve_symbol_references_in_the_descriptions_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Resolve the symbol references in the descriptions in-place."""
    errors = []  # type: List[Error]

    for symbol_ref_in_doc, description, _ in _find_all_in_descriptions(
        element_type=doc.SymbolReference, symbol_table=symbol_table
    ):
        # Symbol references can be repeated as docutils will cache them
        # so we need to skip them.
        if not isinstance(symbol_ref_in_doc.symbol, _PlaceholderSymbol):
            continue

        raw_identifier = symbol_ref_in_doc.symbol.name
        if not raw_identifier.startswith("."):
            errors.append(
                Error(
                    description.parsed.node,
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
                    description.parsed.node,
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
                    description.parsed.node,
                    f"The identifier of the symbol reference "
                    f"could not be found in the symbol table: {identifier}",
                )
            )
            continue

        symbol_ref_in_doc.symbol = referenced_symbol

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
    """
    Resolve the resulting class of the ``specified_for`` in-place.

    This is done both for properties and for methods.
    """
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

                # NOTE (mristin, 2022-01-02):
                # We have to override the ``specified_for`` as we could not set it
                # during the first pass of the translation phase. The ``Final`` in
                # this context is meant for the users of the translation phase, not
                # the translation phase itself.

                specified_for = symbol_table.must_find(
                    Identifier(prop.specified_for.name)
                )
                assert isinstance(specified_for, Class)

                # noinspection PyFinal
                prop.specified_for = specified_for

            for method in symbol.methods:
                assert isinstance(method.specified_for, _PlaceholderSymbol), (
                    f"Expected the placeholder symbol for ``specified_for`` in "
                    f"the method {method} of {symbol}, but got: {method.specified_for}"
                )

                # NOTE (mristin, 2022-01-02):
                # We have to override the ``specified_for`` as we could not set it
                # during the first pass of the translation phase. The ``Final`` in
                # this context is meant for the users of the translation phase, not
                # the translation phase itself.

                specified_for = symbol_table.must_find(
                    name=Identifier(method.specified_for.name)
                )
                assert isinstance(specified_for, Class)

                # noinspection PyFinal
                method.specified_for = specified_for
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

        elif isinstance(symbol, (AbstractClass, ConcreteClass)):
            resolved_class_inheritances = []  # type: List[ClassUnion]

            for inheritance_name in symbol.parsed.inheritances:
                inheritance_symbol = symbol_table.must_find(
                    Identifier(inheritance_name)
                )

                assert isinstance(inheritance_symbol, (AbstractClass, ConcreteClass))
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
            for parsed_descendant in ontology.list_descendants(symbol.parsed):
                descendant = symbol_table.must_find(parsed_descendant.name)
                assert isinstance(descendant, ConstrainedPrimitive)
                constrained_primitive_descendants.append(descendant)

            symbol._set_descendants(constrained_primitive_descendants)

        elif isinstance(symbol, Class):
            class_descendants = []  # type: List[ClassUnion]
            for parsed_descendant in ontology.list_descendants(symbol.parsed):
                descendant = symbol_table.must_find(parsed_descendant.name)
                assert isinstance(descendant, (AbstractClass, ConcreteClass))
                class_descendants.append(descendant)

            symbol._set_descendants(class_descendants)

        else:
            assert_never(symbol)


T = TypeVar("T")


class _SettingWithSource(Generic[T]):
    """
    Represent a setting from an inheritance chain.

    For example, a setting for JSON serialization.
    """

    def __init__(self, value: T, source: ClassUnion):
        """Initialize with the given values."""
        self.value = value
        self.source = source

    def __repr__(self) -> str:
        return (
            f"{_SettingWithSource.__name__}("
            f"value={self.value!r}, "
            f"source={self.source.name!r}"
            f")"
        )


def _second_pass_to_stack_serializations_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Pass on the serializations among the classes along the ontology."""
    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols_topologically_sorted:
        # NOTE (mristin, 2022-03-18):
        # Assume that the parents have all the serializations resolved already due to
        # the topological order of the iteration.

        if isinstance(symbol, (Enumeration, ConstrainedPrimitive)):
            continue
        elif isinstance(symbol, (AbstractClass, ConcreteClass)):
            # NOTE (mristin, 2021-11-03):
            # We do not abstract away different serialization settings at this point
            # as there is only a single one, ``with_model_type``. In the future,
            # if there are more settings, this function needs to be split into multiple
            # ones (one function for a setting each), or maybe we can even think of a
            # more general approach to inheritance of serialization settings.

            with_model_types = []  # type: List[_SettingWithSource[bool]]

            for inheritance in symbol.inheritances:
                if (
                    inheritance.serialization is not None
                    and inheritance.serialization.with_model_type is not None
                ):
                    with_model_types.append(
                        _SettingWithSource(
                            value=inheritance.serialization.with_model_type,
                            source=inheritance,
                        )
                    )

            if (
                symbol.serialization is not None
                and symbol.serialization.with_model_type is not None
            ):
                with_model_types.append(
                    _SettingWithSource(
                        value=symbol.serialization.with_model_type, source=symbol
                    )
                )

            if len(with_model_types) > 0:
                # region Verify that the with_model_type is consistent

                cursor = iter(with_model_types)
                first = next(cursor)

                success = True
                lookahead = next(cursor, None)
                while lookahead is not None:
                    if lookahead.value != first.value:
                        errors.append(
                            Error(
                                symbol.parsed.node,
                                f"The serialization setting ``with_model_type`` "
                                f"between the class {lookahead.source.name!r} "
                                f"and {first.source.name!r} is "
                                f"inconsistent: {lookahead.value!r} != {first.value!r}",
                            )
                        )
                        success = False
                        break

                    lookahead = next(cursor, None)

                if not success:
                    continue

                # endregion

                # Propagate the inferred value to the symbol
                if symbol.serialization is None:
                    symbol.serialization = Serialization(with_model_type=first.value)
                else:
                    symbol.serialization.with_model_type = first.value

        else:
            assert_never(symbol)

    if len(errors) > 0:
        return errors

    # region Set to default values wherever there was no serialization set

    for symbol in symbol_table.symbols_topologically_sorted:
        # NOTE (mristin, 2022-03-18):
        # Assume that the parents have all the serializations resolved already due to
        # the topological order of the iteration.

        if isinstance(symbol, (Enumeration, ConstrainedPrimitive)):
            continue
        elif isinstance(symbol, (AbstractClass, ConcreteClass)):
            if symbol.serialization is None:
                symbol.serialization = Serialization(with_model_type=False)
            else:
                if symbol.serialization.with_model_type is None:
                    symbol.serialization.with_model_type = False
        else:
            assert_never(symbol)

    # endregion

    return errors


def _second_pass_to_stack_invariants_in_place(symbol_table: SymbolTable) -> None:
    """Pass on the invariants among the classes along the ontology."""
    for symbol in symbol_table.symbols_topologically_sorted:
        # NOTE (mristin, 2022-03-18):
        # Assume that the parents have all the invariants stacked already due to
        # the topological order of the iteration..

        # Propagate the invariants from the parents to this symbol.
        if isinstance(symbol, Enumeration):
            continue
        elif isinstance(symbol, (ConstrainedPrimitive, AbstractClass, ConcreteClass)):
            inherited_invariants = []  # type: List[Invariant]

            # NOTE (mristin, 2022-03-18):
            # Skip duplicates which might arise from the diamond inheritance
            observed_invariants = set()  # type: Set[int]

            for inheritance in symbol.inheritances:
                for invariant in inheritance.invariants:
                    invariant_id = id(invariant)
                    if invariant_id not in observed_invariants:
                        inherited_invariants.append(invariant)
                        observed_invariants.add(invariant_id)

            symbol._set_invariants(
                list(itertools.chain(inherited_invariants, symbol.invariants))
            )
        else:
            assert_never(symbol)


def _second_pass_to_stack_properties_in_place(symbol_table: SymbolTable) -> List[Error]:
    """Pass on the properties among the classes along the ontology."""
    for symbol in symbol_table.symbols_topologically_sorted:
        # NOTE (mristin, 2022-03-18):
        # Assume that the parents have all the invariants stacked already due to
        # the topological order of the iteration..

        # Propagate the properties from the parents to this symbol.
        if isinstance(symbol, (Enumeration, ConstrainedPrimitive)):
            continue
        elif isinstance(symbol, (AbstractClass, ConcreteClass)):
            inherited_properties = []  # type: List[Property]

            # NOTE (mristin, 2022-03-18):
            # Skip duplicates which might arise from the diamond inheritance
            observed_properties = set()  # type: Set[int]

            for inheritance in symbol.inheritances:
                for prop in inheritance.properties:
                    property_id = id(prop)
                    if property_id not in observed_properties:
                        inherited_properties.append(prop)
                        observed_properties.add(property_id)

            symbol._set_properties(
                list(itertools.chain(inherited_properties, symbol.properties))
            )
        else:
            assert_never(symbol)

    return []


def _second_pass_to_stack_methods_in_place(symbol_table: SymbolTable) -> List[Error]:
    """Pass on the methods among the classes along the ontology."""
    errors = []  # type: List[Error]
    for symbol in symbol_table.symbols_topologically_sorted:
        # NOTE (mristin, 2022-03-18):
        # Assume that the parents have all the invariants stacked already due to
        # the topological order of the iteration..

        # Propagate the methods from the parents to this symbol.
        if isinstance(symbol, (Enumeration, ConstrainedPrimitive)):
            continue
        elif isinstance(symbol, (AbstractClass, ConcreteClass)):
            inherited_methods = []  # type: List[MethodUnion]

            # NOTE (mristin, 2022-03-19):
            # We have to disallow diamond inheritance of the methods so we keep track
            # of the inherited methods and report an error in case of conflicts.

            method_specified_for = dict()  # type: Dict[Identifier, Identifier]
            for inheritance in symbol.inheritances:
                for method in inheritance.methods:
                    conflicting_parent = method_specified_for.get(method.name, None)
                    if conflicting_parent is not None:
                        errors.append(
                            Error(
                                symbol.parsed.node,
                                f"The method {method.name!r} can not be inherited "
                                f"in the class {symbol.name!r} due to "
                                f"the diamond inheritance both "
                                f"from the parent {inheritance.name} and "
                                f"from the parent {conflicting_parent}",
                            )
                        )
                        continue

                    inherited_methods.append(method)
                    method_specified_for[method.name] = inheritance.name

            # NOTE (mristin, 2022-03-19):
            # We still haven't updated the ``methods`` in the symbol so it only
            # contains methods specified for that particular class and does not
            # include any inherited methods.

            has_override = False
            for method in symbol.methods:
                conflicting_parent = method_specified_for.get(method.name, None)
                if conflicting_parent is not None:
                    errors.append(
                        Error(
                            method.parsed.node,
                            f"We do not support the overriding of the methods, "
                            f"but the method {method.name!r} is specified both in "
                            f"the class {symbol.name!r} and in {conflicting_parent!r}; "
                            f"if you need this functionality please contact "
                            f"the developers.",
                        )
                    )
                    has_override = True

            if has_override:
                continue

            symbol._set_methods(
                list(itertools.chain(inherited_methods, symbol.methods))
            )
        else:
            assert_never(symbol)

    return errors


def _second_pass_to_stack_constructors_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """In-line the super constructors and inherit the constructor contracts."""
    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        # NOTE (mristin, 2022-03-18):
        # Assume that the parents have all been processed already due to
        # the topological order of the iteration..

        if isinstance(symbol, (Enumeration, ConstrainedPrimitive)):
            continue
        elif isinstance(symbol, (AbstractClass, ConcreteClass)):

            # region In-line super constructors

            in_lined = []  # type: List[construction.AssignArgument]

            for statement in symbol.constructor.statements:
                if isinstance(statement, construction.CallSuperConstructor):
                    ancestor = symbol_table.find(statement.super_name)

                    assert isinstance(ancestor, (AbstractClass, ConcreteClass)), (
                        f"Expected the ancestor of a class {symbol.name!r} "
                        f"to be a class, but got: {ancestor}"
                    )

                    if ancestor is None:
                        errors.append(
                            Error(
                                symbol.constructor.parsed.node
                                if symbol.constructor.parsed is not None
                                else symbol.parsed.node,
                                f"In the constructor of the class {symbol.name!r} "
                                f"the super-constructor for "
                                f"the class {statement.super_name!r} is invoked, "
                                f"but the class {statement.super_name!r} could not "
                                f"be found",
                            )
                        )
                        continue

                    if id(ancestor) not in symbol.inheritance_id_set:
                        errors.append(
                            Error(
                                symbol.constructor.parsed.node
                                if symbol.constructor.parsed is not None
                                else symbol.parsed.node,
                                f"In the constructor of the class {symbol.name!r} "
                                f"the super-constructor for "
                                f"the class {statement.super_name!r} is invoked, "
                                f"but the class {statement.super_name!r} is not "
                                f"a direct parent of the class {symbol.name!r}",
                            )
                        )
                        continue

                    assert all(
                        not isinstance(a_statement, construction.CallSuperConstructor)
                        for a_statement in ancestor.constructor.statements
                    ), (
                        f"Expected all the calls to super-constructors to be in-lined "
                        f"in the ancestor {ancestor.name} of the class {symbol.name}"
                    )

                    in_lined.extend(ancestor.constructor.statements)
                else:
                    in_lined.append(statement)

            # NOTE (mristin, 2022-03-19):
            # Restore the type safety at run-time
            assert all(
                isinstance(stmt, construction.AssignArgument) for stmt in in_lined
            )

            # NOTE (mristin, 2022-03-18):
            # The ``Final`` qualifier is meant for the external clients, not for the
            # internal clients in the submodules.
            # noinspection PyFinal,PyTypeHints
            symbol.constructor.statements = in_lined  # type: ignore

            # endregion

            # region Stack contracts

            # NOTE (mristin, 2022-03-19):
            # The pre-conditions are not inherited in the constructors.
            # See a tutorial on design-by-contract. However, we do in-line
            # the calls to the super constructors. We leave it to the user to maintain
            # the list of pre-conditions and copy/paste them from the ancestors
            # manually.

            inherited_snapshots = []  # type: List[Snapshot]
            inherited_postconditions = []  # type: List[Contract]

            # NOTE (mristin, 2022-03-19):
            # We skip the duplicates since we have to deal with the diamond inheritance.
            observed_snapshots = set()  # type: Set[int]
            observed_postconditions = set()  # type: Set[int]

            for inheritance in symbol.inheritances:
                for snapshot in inheritance.constructor.contracts.snapshots:
                    snapshot_id = id(snapshot)
                    if snapshot_id not in observed_snapshots:
                        inherited_snapshots.append(snapshot)
                        observed_snapshots.add(snapshot_id)

                for postcondition in inheritance.constructor.contracts.postconditions:
                    postcondition_id = id(postcondition)
                    if postcondition_id not in observed_postconditions:
                        inherited_postconditions.append(postcondition)
                        observed_postconditions.add(postcondition_id)

            # NOTE (mristin, 2022-03-18):
            # The ``Final`` qualifier is meant for the external clients, not for the
            # internal clients in the submodules.

            # noinspection PyFinal
            symbol.constructor.contracts.snapshots = list(  # type: ignore
                itertools.chain(
                    inherited_snapshots, symbol.constructor.contracts.snapshots
                )
            )

            # noinspection PyFinal
            symbol.constructor.contracts.postconditions = list(  # type: ignore
                itertools.chain(
                    inherited_postconditions,
                    symbol.constructor.contracts.postconditions,
                )
            )

            # endregion
        else:
            assert_never(symbol)

    return errors


def _second_pass_to_resolve_attribute_references_in_the_descriptions_in_place(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Resolve the attribute references in the descriptions in-place."""
    errors = []  # type: List[Error]

    # The ``symbol`` is None if the description is in the context outside of a symbol.
    for attr_ref_in_doc, description, symbol in _find_all_in_descriptions(
        element_type=doc.AttributeReference, symbol_table=symbol_table
    ):
        # BEFORE-RELEASE (mristin, 2021-12-13):
        #  test this, especially the failure cases
        if isinstance(attr_ref_in_doc.reference, _PlaceholderAttributeReference):
            pth = attr_ref_in_doc.reference.path
            parts = pth.split(".")

            if any(not IDENTIFIER_RE.match(part) for part in parts):
                errors.append(
                    Error(
                        description.parsed.node,
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
                        description.parsed.node,
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
                            description.parsed.node,
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
                            description.parsed.node,
                            f"Dangling reference to a non-existing " f"symbol: {pth}",
                        )
                    )
                    continue

                attr_identifier = part_identifiers[1]
            else:
                errors.append(
                    Error(
                        description.parsed.node,
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
                            description.parsed.node,
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
                        description.parsed.node,
                        f"Unexpected references to a property of "
                        f"a constrained primitive {target_symbol.name!r}: {pth}",
                    )
                )
                continue

            elif isinstance(target_symbol, (AbstractClass, ConcreteClass)):
                prop = target_symbol.properties_by_name.get(attr_identifier, None)

                if prop is None:
                    errors.append(
                        Error(
                            description.parsed.node,
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


def _verify_there_are_no_duplicate_symbol_names(
    symbol_table: SymbolTable,
) -> List[Error]:
    errors = []  # type: List[Error]

    observed_names = dict()  # type: MutableMapping[Identifier, Symbol]
    for symbol in symbol_table.symbols:
        other_symbol = observed_names.get(symbol.name, None)
        if other_symbol is None:
            observed_names[symbol.name] = symbol
        else:
            errors.append(
                Error(
                    symbol.parsed.node,
                    f"The symbol with the name {symbol.name!r} conflicts with "
                    f"other symbol with the same name.",
                )
            )

    return errors


def _verify_with_model_type_for_classes_with_at_least_one_concrete_descendant(
    symbol_table: SymbolTable,
) -> List[Error]:
    errors = []  # type: List[Error]

    symbols_in_properties = collect_ids_of_symbols_in_properties(
        symbol_table=symbol_table
    )

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        if id(symbol) in symbols_in_properties:
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

    return errors


def _verify_all_the_function_calls_in_the_contracts_are_valid(
    symbol_table: SymbolTable,
) -> List[Error]:
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

    return contract_checker.errors


def _verify_all_non_optional_properties_initialized(cls: Class) -> List[Error]:
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


def _verify_all_non_optional_properties_are_initialized_in_the_constructor(
    symbol_table: SymbolTable,
) -> List[Error]:
    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        errors.extend(_verify_all_non_optional_properties_initialized(cls=symbol))

    return errors


def _verify_orders_of_constructors_arguments_and_properties_match(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Verify the order between the constructor arguments and the properties."""
    errors = []  # type: List[Error]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, (Enumeration, ConstrainedPrimitive)):
            continue
        elif isinstance(symbol, (AbstractClass, ConcreteClass)):
            args_without_default = []  # type: List[Identifier]
            args_without_default_set = set()  # type: Set[Identifier]

            args_with_default = []  # type: List[Identifier]
            args_with_default_set = set()  # type: Set[Identifier]

            # NOTE (mristin, 2022-03-25):
            # This verification is only a heuristic since we do not really analyze
            # the code and only look into the names of the properties and arguments.

            for arg in symbol.constructor.arguments:
                if arg.name not in symbol.properties_by_name:
                    continue

                if arg.default is None:
                    args_without_default.append(arg.name)
                    args_without_default_set.add(arg.name)
                else:
                    args_with_default.append(arg.name)
                    args_with_default_set.add(arg.name)

            # The order of the properties corresponding to the constructor
            # arguments without the default value
            props_without_default = [
                prop.name
                for prop in symbol.properties
                if prop.name in args_without_default_set
            ]

            # The order of the properties corresponding to the constructor arguments
            # with the specified default value
            props_with_default = [
                prop.name
                for prop in symbol.properties
                if prop.name in args_with_default_set
            ]

            ordered_args = args_without_default + args_with_default
            ordered_props = props_without_default + props_with_default

            if ordered_args != ordered_props:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"The order of constructor arguments and properties "
                        f"for the class {symbol.name!r} is not maintained "
                        f"where they match by name. "
                        f"The partial order of constructor arguments "
                        f"should be: {ordered_props!r}",
                    )
                )
        else:
            assert_never(symbol)

    return errors


def _verify_all_argument_references_occur_in_valid_context(
    symbol_table: SymbolTable,
) -> List[Error]:
    """Verify that all the argument references occur where they should."""
    errors = []  # type: List[Error]
    for arg_ref_in_doc, description, _ in _find_all_in_descriptions(
        element_type=doc.ArgumentReference, symbol_table=symbol_table
    ):
        if not isinstance(description, SignatureDescription):
            errors.append(
                Error(
                    description.parsed.node,
                    f"Unexpected argument reference in the description of "
                    f"a non-signature (*i.e.*, a non-function and a non-method): "
                    f"{arg_ref_in_doc}",
                )
            )

    return errors


def _verify_constraints_and_constraintrefs(symbol_table: SymbolTable) -> List[Error]:
    """Check that each constraint has a unique identifier."""
    errors = []  # type: List[Error]
    observed_constraint_id_set = set()  # type: Set[str]

    def check_and_report_duplicate(
        an_identifier: str, a_description: DescriptionUnion
    ) -> None:
        """If the identifier has been already observed, report a duplicate."""
        if an_identifier in observed_constraint_id_set:
            errors.append(
                Error(
                    a_description.parsed.node,
                    f"The constraint with the same identifier has been already "
                    f"defined: {an_identifier!r}",
                )
            )

    if symbol_table.meta_model.description is not None:
        for identifier in symbol_table.meta_model.description.constraints_by_identifier:
            check_and_report_duplicate(
                an_identifier=identifier,
                a_description=symbol_table.meta_model.description,
            )
            observed_constraint_id_set.add(identifier)

    for symbol in symbol_table.symbols:
        if symbol.description is not None:
            for identifier in symbol.description.constraints_by_identifier:
                check_and_report_duplicate(
                    an_identifier=identifier, a_description=symbol.description
                )
                observed_constraint_id_set.add(identifier)

        if isinstance(symbol, (Enumeration, ConstrainedPrimitive)):
            pass
        elif isinstance(symbol, (AbstractClass, ConcreteClass)):
            for prop in symbol.properties:
                if prop.specified_for is not symbol:
                    continue

                if prop.description is not None:
                    for identifier in prop.description.constraints_by_identifier:
                        check_and_report_duplicate(
                            an_identifier=identifier, a_description=prop.description
                        )
                        observed_constraint_id_set.add(identifier)
        else:
            assert_never(symbol)

    for constraintref, description, _ in _find_all_in_descriptions(
        element_type=doc.ConstraintReference, symbol_table=symbol_table
    ):
        assert isinstance(constraintref.reference, str)

        if constraintref.reference not in observed_constraint_id_set:
            errors.append(
                Error(
                    description.parsed.node,
                    f"The constraint reference is dangling: {constraintref.reference}",
                )
            )

    return errors


def _verify_description_rendering_with_smoke(symbol_table: SymbolTable) -> List[Error]:
    """Check that we can smoke-render all the descriptions."""

    class DummyRenderer(rendering.DocutilsElementTransformer[bool]):
        """Perform a smoke rendering to test that all the elements have been covered."""

        def transform_text(
            self, element: docutils.nodes.Text
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_symbol_reference_in_doc(
            self, element: doc.SymbolReference
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_attribute_reference_in_doc(
            self, element: doc.AttributeReference
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_argument_reference_in_doc(
            self, element: doc.ArgumentReference
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_constraint_reference_in_doc(
            self, element: doc.ConstraintReference
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_literal(
            self, element: docutils.nodes.literal
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_paragraph(
            self, element: docutils.nodes.paragraph
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_emphasis(
            self, element: docutils.nodes.emphasis
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_list_item(
            self, element: docutils.nodes.list_item
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_bullet_list(
            self, element: docutils.nodes.bullet_list
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_note(
            self, element: docutils.nodes.note
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_reference(
            self, element: docutils.nodes.reference
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_field_body(
            self, element: docutils.nodes.field_body
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

        def transform_document(
            self, element: docutils.nodes.field_body
        ) -> Tuple[Optional[bool], Optional[List[str]]]:
            return True, None

    renderer = DummyRenderer()

    errors_by_description = (
        collections.OrderedDict()
    )  # type: OrderedDict[DescriptionUnion, List[Error]]

    for an_element, description, _ in _find_all_in_descriptions(
        element_type=docutils.nodes.Element, symbol_table=symbol_table
    ):
        _, transformation_errors = renderer.transform(element=an_element)

        if transformation_errors is not None:
            description_errors = errors_by_description.get(description, None)
            if description_errors is None:
                description_errors = []
                errors_by_description[description] = description_errors

            description_errors.extend(
                Error(description.parsed.node, error_message)
                for error_message in transformation_errors
            )

    errors = []  # type: List[Error]
    for description, description_errors in errors_by_description.items():
        assert len(description_errors) > 0
        errors.append(
            Error(
                description.parsed.node,
                "Failed to test-smoke the rendering of the description",
                description_errors,
            )
        )

    return errors


def _verify_only_simple_type_patterns(symbol_table: SymbolTable) -> List[Error]:
    """
    Check that there are only simple type patterns in the meta-model.

    Namely, for a lot of code generators, unrolling arbitrary type annotations is
    quite complex. In contrast, if we can make simplifying assumptions about the types
    in the meta-model, we can write much simpler generators.

    First, the meta-model is quite limited itself at the moment, so the complexity of
    the general solutions is not warranted. Second, we hope that there will be fewer
    bugs in the simple solution which is particularly important at this early adoption
    stage.

    We anticipate that we will want to actually write the more complex generators
    in the future. At this point, we restrict ourselves to the following patterns:

    * Non-nested optional types, *i.e.* optional of optionals, are unexpected;
    * Lists of optionals are unexpected; and
    * Lists of non-classes are unexpected.
    """
    errors = []  # type: List[Error]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, (AbstractClass, ConcreteClass)):
            for prop in symbol.properties:
                if isinstance(
                    prop.type_annotation, OptionalTypeAnnotation
                ) and isinstance(prop.type_annotation.value, OptionalTypeAnnotation):
                    errors.append(
                        Error(
                            prop.parsed.node,
                            "We currently support only a limited set of "
                            "type annotation patterns. At the moment, we do not handle "
                            "nested optionals. Please contact the developers if you "
                            "need this functionality",
                        )
                    )

                type_anno = beneath_optional(prop.type_annotation)
                if isinstance(type_anno, ListTypeAnnotation):
                    if not (
                        isinstance(type_anno.items, OurTypeAnnotation)
                        and isinstance(
                            type_anno.items.symbol, (AbstractClass, ConcreteClass)
                        )
                    ):
                        errors.append(
                            Error(
                                prop.parsed.node,
                                f"We currently support only a limited set of "
                                f"type annotation patterns. At the moment, we handle "
                                f"only lists of classes (both concrete or abstract), "
                                f"but the property {prop.name!r} "
                                f"of the class {symbol.name!r} "
                                f"has type: {prop.type_annotation}. "
                                f"Please contact the developers if you need "
                                f"this functionality",
                            )
                        )

    return errors


def _assert_interfaces_defined_correctly(
    symbol_table: SymbolTable, ontology: _hierarchy.Ontology
) -> None:
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


def _assert_all_class_inheritances_defined_an_interface(
    symbol_table: SymbolTable,
) -> None:
    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        for inheritance in symbol.inheritances:
            assert isinstance(inheritance.interface, Interface), (
                f"Since the class {symbol.name!r} inherits from {inheritance.name!r}, "
                f"we expect that the class {inheritance.name!r} also has an interface "
                f"defined for it, but it does not."
            )


def _assert_self_not_in_concrete_descendants(symbol_table: SymbolTable) -> None:
    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue
        elif isinstance(symbol, (ConstrainedPrimitive, AbstractClass, ConcreteClass)):
            assert id(symbol) not in symbol.descendant_id_set, (
                f"Expected not to find the ID of the symbol {symbol!r}, {id(symbol)} "
                f"in its descendant_id_set, "
                f"but it was there: {symbol.descendant_id_set}"
            )

            if isinstance(symbol, ConcreteClass):
                assert symbol not in symbol.concrete_descendants, (
                    f"Expected not to find the symbol {symbol!r} "
                    f"in its concrete descendants, "
                    f"but it was there: {symbol.concrete_descendants}"
                )
        else:
            assert_never(symbol)


def _verify(symbol_table: SymbolTable, ontology: _hierarchy.Ontology) -> List[Error]:
    """Perform a battery of checks on the consistency of ``symbol_table``."""
    errors = _verify_there_are_no_duplicate_symbol_names(symbol_table=symbol_table)

    if len(errors) > 0:
        return errors

    errors.extend(
        _verify_with_model_type_for_classes_with_at_least_one_concrete_descendant(
            symbol_table=symbol_table
        )
    )

    errors.extend(
        _verify_all_the_function_calls_in_the_contracts_are_valid(
            symbol_table=symbol_table
        )
    )

    errors.extend(
        _verify_all_non_optional_properties_are_initialized_in_the_constructor(
            symbol_table=symbol_table
        )
    )

    errors.extend(
        _verify_orders_of_constructors_arguments_and_properties_match(
            symbol_table=symbol_table
        )
    )

    errors.extend(
        _verify_all_argument_references_occur_in_valid_context(
            symbol_table=symbol_table
        )
    )

    errors.extend(_verify_constraints_and_constraintrefs(symbol_table=symbol_table))

    errors.extend(_verify_description_rendering_with_smoke(symbol_table=symbol_table))

    errors.extend(_verify_only_simple_type_patterns(symbol_table=symbol_table))

    if len(errors) > 0:
        return errors

    _assert_interfaces_defined_correctly(symbol_table=symbol_table, ontology=ontology)

    _assert_all_class_inheritances_defined_an_interface(symbol_table=symbol_table)

    _assert_self_not_in_concrete_descendants(symbol_table=symbol_table)

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

    # region Understand constructors

    constructor_table, constructor_error = construction.understand_all(
        parsed_symbol_table=parsed_symbol_table, atok=atok
    )

    if constructor_error is not None:
        underlying_errors.append(constructor_error)

    # endregion

    if len(underlying_errors) > 0:
        # We can not proceed and recover from these errors as they concern critical
        # dependencies of the further analysis.
        return None, bundle_underlying_errors()

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

    # endregion

    # region First pass of translation

    assert constructor_table is not None
    assert constrained_primitives_by_name is not None

    # Type annotations reference symbol placeholders at this point.

    symbols = []  # type: List[Symbol]
    for parsed_symbol in parsed_symbol_table.symbols:
        symbol = None  # type: Optional[Symbol]

        constrainee = constrained_primitives_by_name.get(parsed_symbol.name, None)

        if constrainee is not None:
            assert isinstance(
                parsed_symbol, parse.ConcreteClass
            ), "All constrained primitive types must be concrete."

            symbol, parsing_errors = _to_constrained_primitive(
                parsed=parsed_symbol, constrainee=constrainee
            )
            if parsing_errors is not None:
                underlying_errors.append(
                    Error(
                        parsed_symbol.node,
                        f"Failed to translate "
                        f"the constrained primitive {parsed_symbol.name}",
                        parsing_errors,
                    )
                )
                continue

        elif isinstance(parsed_symbol, parse.Enumeration):
            symbol, symbol_errors = _to_enumeration(parsed=parsed_symbol)
            if symbol_errors is not None:
                underlying_errors.append(
                    Error(
                        parsed_symbol.node,
                        f"Failed to translate the enumeration {parsed_symbol.name!r}",
                        symbol_errors,
                    )
                )
                continue

        elif isinstance(parsed_symbol, (parse.AbstractClass, parse.ConcreteClass)):
            symbol, symbol_errors = _to_class(
                parsed=parsed_symbol,
                constructor_statements=constructor_table.must_find(parsed_symbol),
            )

            if symbol_errors is not None:
                underlying_errors.append(
                    Error(
                        parsed_symbol.node,
                        f"Failed to translate the class {parsed_symbol.name!r}",
                        symbol_errors,
                    )
                )
                continue

        else:
            assert_never(parsed_symbol)

        assert symbol is not None
        symbols.append(symbol)

    meta_model, meta_model_errors = _to_meta_model(
        parsed=parsed_symbol_table.meta_model
    )
    if meta_model_errors is not None:
        underlying_errors.append(
            Error(
                None,
                "Failed to translate the meta-data of the meta-model",
                meta_model_errors,
            )
        )

    verification_functions = []  # type: List[VerificationUnion]
    for func in parsed_symbol_table.verification_functions:
        verification, verification_errors = _to_verification_function(func)

        if verification_errors is not None:
            underlying_errors.append(
                Error(
                    func.node,
                    f"Failed to translate the verification function {func.name!r}",
                    verification_errors,
                )
            )
            continue

        assert verification is not None
        verification_functions.append(verification)

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    assert meta_model is not None

    symbols_by_name = {symbol.name: symbol for symbol in symbols}

    symbols_topologically_sorted = []  # type: List[SymbolExceptEnumeration]
    for parsed_cls in ontology.classes:
        symbol = symbols_by_name[parsed_cls.name]
        assert not isinstance(symbol, Enumeration)
        symbols_topologically_sorted.append(symbol)

    symbol_table = SymbolTable(
        symbols=symbols,
        symbols_topologically_sorted=symbols_topologically_sorted,
        verification_functions=verification_functions,
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

    # region Second passes which do not require the heritage to be inherited

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

    # endregion

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    # region Second passes to inherit the heritage

    underlying_errors.extend(
        _second_pass_to_stack_serializations_in_place(symbol_table=symbol_table)
    )

    _second_pass_to_stack_invariants_in_place(symbol_table=symbol_table)

    underlying_errors.extend(
        _second_pass_to_stack_properties_in_place(symbol_table=symbol_table)
    )

    underlying_errors.extend(
        _second_pass_to_stack_methods_in_place(symbol_table=symbol_table)
    )

    underlying_errors.extend(
        _second_pass_to_stack_constructors_in_place(symbol_table=symbol_table)
    )

    # endregion

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    # region Second passes which assume the inheritance of the heritage

    # NOTE (mristin, 2022-03-18):
    # We might reference inherited properties of a symbol so we need to apply
    # this second pass only after the properties have been stacked.
    underlying_errors.extend(
        _second_pass_to_resolve_attribute_references_in_the_descriptions_in_place(
            symbol_table=symbol_table
        )
    )

    # NOTE (mristin, 2022-03-18):
    # We need to include all the properties and methods in the interface so they need
    # to be inherited first.
    _second_pass_to_resolve_interfaces_in_place(
        symbol_table=symbol_table, ontology=ontology
    )

    # endregion

    underlying_errors.extend(_verify(symbol_table=symbol_table, ontology=ontology))

    if len(underlying_errors) > 0:
        return None, bundle_underlying_errors()

    return symbol_table, None


def errors_if_contracts_for_functions_or_methods_defined(
    symbol_table: SymbolTable,
) -> Optional[List[Error]]:
    """
    Generate an error if one or more contracts for functions or methods defined.

    This does *not* apply to implementation-specific functions as they are going to
    be manually implemented and we do not have to transpile them.

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
            # NOTE (mristin, 2022-05-18):
            # We allow implementation-specific methods to have pre- and post-conditions
            # as they are used only for documentation, but are not transpiled.
            if isinstance(
                signature_like,
                (ImplementationSpecificVerification, ImplementationSpecificMethod),
            ):
                continue

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
