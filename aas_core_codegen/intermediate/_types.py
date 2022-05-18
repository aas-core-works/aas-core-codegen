"""Provide types of the intermediate representation."""
import abc
import enum
import pathlib
from typing import (
    Sequence,
    Optional,
    Union,
    TypeVar,
    Mapping,
    MutableMapping,
    Final,
    FrozenSet,
    Set,
    Tuple,
    OrderedDict,
    List,
)

import docutils.nodes
from icontract import require, invariant, ensure, DBC

from aas_core_codegen import parse
from aas_core_codegen.common import (
    Identifier,
    assert_never,
    assert_union_of_descendants_exhaustive,
    assert_union_without_excluded,
)
from aas_core_codegen.intermediate import construction
from aas_core_codegen.parse import tree as parse_tree

_MODULE_NAME = pathlib.Path(__file__).parent.name


class PrimitiveType(enum.Enum):
    """List primitive types."""

    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    BYTEARRAY = "bytearray"


assert sorted(literal.value for literal in PrimitiveType) == sorted(
    parse.PRIMITIVE_TYPES
), "All primitive types specified in the intermediate layer"

STR_TO_PRIMITIVE_TYPE = {
    literal.value: literal for literal in PrimitiveType
}  # type: Mapping[str, PrimitiveType]


class TypeAnnotation(DBC):
    """Represent a general type annotation."""

    #: Relation to the parse stage
    parsed: Final[parse.TypeAnnotation]

    def __init__(self, parsed: parse.TypeAnnotation) -> None:
        """Initialize with the given values."""
        self.parsed = parsed

    @abc.abstractmethod
    def __str__(self) -> str:
        # Signal that this class is a purely abstract one
        raise NotImplementedError()


class PrimitiveTypeAnnotation(TypeAnnotation):
    """Represent a primitive type such as ``int``."""

    def __init__(self, a_type: PrimitiveType, parsed: parse.TypeAnnotation) -> None:
        """Initialize with the given values."""
        TypeAnnotation.__init__(self, parsed=parsed)
        self.a_type = a_type

    def __str__(self) -> str:
        return str(self.a_type.value)


class OurTypeAnnotation(TypeAnnotation):
    """
    Represent an atomic annotation defined by a symbol in the meta-model.

     For example, ``Asset``.
    """

    def __init__(self, symbol: "Symbol", parsed: parse.TypeAnnotation) -> None:
        """Initialize with the given values."""
        TypeAnnotation.__init__(self, parsed=parsed)
        self.symbol = symbol

    def __str__(self) -> str:
        return self.symbol.name


class ListTypeAnnotation(TypeAnnotation):
    """Represent a type annotation involving a ``List[...]``."""

    def __init__(self, items: "TypeAnnotationUnion", parsed: parse.TypeAnnotation):
        TypeAnnotation.__init__(self, parsed=parsed)

        self.items = items

    def __str__(self) -> str:
        return f"List[{self.items}]"


# NOTE (mristin, 2021-11-19):
# We do not support other generic types except for ``List``. In the future we might
# add support for ``Set``, ``MutableMapping`` *etc.*


class OptionalTypeAnnotation(TypeAnnotation):
    """Represent a type annotation involving an ``Optional[...]``."""

    def __init__(self, value: "TypeAnnotationUnion", parsed: parse.TypeAnnotation):
        TypeAnnotation.__init__(self, parsed=parsed)

        self.value = value

    def __str__(self) -> str:
        return f"Optional[{self.value}]"


TypeAnnotationUnion = Union[
    PrimitiveTypeAnnotation,
    OurTypeAnnotation,
    ListTypeAnnotation,
    OptionalTypeAnnotation,
]


assert_union_of_descendants_exhaustive(
    union=TypeAnnotationUnion, base_class=TypeAnnotation
)


TypeAnnotationExceptOptional = Union[
    PrimitiveTypeAnnotation,
    OurTypeAnnotation,
    ListTypeAnnotation,
]

assert_union_without_excluded(
    original_union=TypeAnnotationUnion,
    subset_union=TypeAnnotationExceptOptional,
    excluded=[OptionalTypeAnnotation],
)

AtomicTypeAnnotation = Union[PrimitiveTypeAnnotation, OurTypeAnnotation]

assert_union_without_excluded(
    original_union=TypeAnnotationUnion,
    subset_union=AtomicTypeAnnotation,
    excluded=[ListTypeAnnotation, OptionalTypeAnnotation],
)


def type_annotations_equal(
    that: TypeAnnotationUnion, other: TypeAnnotationUnion
) -> bool:
    """
    Compare two type annotations for equality.

    Two type annotations are equal if they describe the same type.
    """
    if type(that) is not type(other):
        return False

    if isinstance(that, PrimitiveTypeAnnotation):
        assert isinstance(other, PrimitiveTypeAnnotation)
        return that.a_type == other.a_type

    elif isinstance(that, OurTypeAnnotation):
        assert isinstance(other, OurTypeAnnotation)
        return that.symbol == other.symbol

    elif isinstance(that, ListTypeAnnotation):
        assert isinstance(other, ListTypeAnnotation)
        return type_annotations_equal(that.items, other.items)

    elif isinstance(that, OptionalTypeAnnotation):
        assert isinstance(other, OptionalTypeAnnotation)
        return type_annotations_equal(that.value, other.value)

    else:
        assert_never(that)

    raise AssertionError("Should not have gotten here")


def beneath_optional(
    type_annotation: TypeAnnotationUnion,
) -> TypeAnnotationExceptOptional:
    """Descend below ``Optional[...]`` to the underlying type."""
    type_anno = type_annotation
    while isinstance(type_anno, OptionalTypeAnnotation):
        type_anno = type_anno.value

    assert not isinstance(type_anno, OptionalTypeAnnotation)

    return type_anno


# region Descriptions

# NOTE (mristin, 2022-03-18):
# We take C# documentation comments as an orientation for the structure of the
# descriptions.


def find_first_field_list(
    element: docutils.nodes.Element,
) -> Optional[docutils.nodes.field_list]:
    """Find the first field list beneath the element or return None."""
    return next(element.findall(condition=docutils.nodes.field_list), None)


class SummaryRemarksDescription(DBC):
    """Represent a description with a summary and remarks."""

    #: Summary as the first line of the docstring
    summary: Final[docutils.nodes.paragraph]

    #: List of remarks following the summary in the docstring
    remarks: Final[Sequence[docutils.nodes.Element]]

    #: Original parsed description
    parsed: Final[parse.Description]

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
    # fmt: on
    def __init__(
        self,
        summary: docutils.nodes.paragraph,
        remarks: Sequence[docutils.nodes.Element],
        parsed: parse.Description,
    ) -> None:
        """Initialize with the given values."""
        self.summary = summary
        self.remarks = remarks
        self.parsed = parsed

    @abc.abstractmethod
    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        raise NotImplementedError()


# noinspection PyAbstractClass
class SummaryRemarksConstraintsDescription(SummaryRemarksDescription):
    """Represent a description with summary, remarks and constraints blocks."""

    #: Map constraint documentation elements by their identifiers
    constraints_by_identifier: Final[OrderedDict[str, docutils.nodes.field_body]]

    # fmt: off
    @require(
        lambda constraints_by_identifier:
        all(
            find_first_field_list(body) is None
            for body in constraints_by_identifier.values()
        ),
        "Constraint bodies expected without field lists"
    )
    # fmt: on
    def __init__(
        self,
        summary: docutils.nodes.paragraph,
        remarks: Sequence[docutils.nodes.Element],
        constraints_by_identifier: OrderedDict[str, docutils.nodes.field_body],
        parsed: parse.Description,
    ) -> None:
        """Initialize with the given values."""
        SummaryRemarksDescription.__init__(
            self, summary=summary, remarks=remarks, parsed=parsed
        )
        self.constraints_by_identifier = constraints_by_identifier


class MetaModelDescription(SummaryRemarksConstraintsDescription):
    """Represent a description of a meta-model."""

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return f"<{_MODULE_NAME}.{self.__class__.__name__} at 0x{id(self):x}>"


class SymbolDescription(SummaryRemarksConstraintsDescription):
    """Represent a description of a symbol."""

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return f"<{_MODULE_NAME}.{self.__class__.__name__} at 0x{id(self):x}>"


class PropertyDescription(SummaryRemarksConstraintsDescription):
    """Represent a documentation of a property."""

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return f"<{_MODULE_NAME}.{self.__class__.__name__} at 0x{id(self):x}>"


class EnumerationLiteralDescription(SummaryRemarksDescription):
    """Represent a documentation of an enumeration literal."""

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return f"<{_MODULE_NAME}.{self.__class__.__name__} at 0x{id(self):x}>"


class SignatureDescription(SummaryRemarksDescription):
    """Represent a documentation of a method or a function signature."""

    #: Map argument documentation by the argument names
    arguments_by_name: Final[OrderedDict[Identifier, docutils.nodes.field_body]]

    #: Documentation of the return value, if written
    returns: Final[Optional[docutils.nodes.field_body]]

    # fmt: off
    @require(
        lambda arguments_by_name:
        all(
            find_first_field_list(body) is None
            for body in arguments_by_name.values()
        ),
        "Argument descriptions expected without field lists"
    )
    @require(
        lambda returns:
        not (returns is not None)
        or find_first_field_list(returns) is None,
        "Return value description expected without field lists"
    )
    # fmt: on
    def __init__(
        self,
        summary: docutils.nodes.paragraph,
        remarks: Sequence[docutils.nodes.Element],
        arguments_by_name: OrderedDict[Identifier, docutils.nodes.field_body],
        returns: Optional[docutils.nodes.field_body],
        parsed: parse.Description,
    ) -> None:
        """Initialize with the given values."""
        SummaryRemarksDescription.__init__(
            self, summary=summary, remarks=remarks, parsed=parsed
        )
        self.arguments_by_name = arguments_by_name
        self.returns = returns

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return f"<{_MODULE_NAME}.{self.__class__.__name__} at 0x{id(self):x}>"


# endregion


class Property:
    """Represent a property of a class."""

    #: Name of the property
    name: Final[Identifier]

    #: Type annotation of the property
    type_annotation: Final[TypeAnnotationUnion]

    #: Description of the property, if any
    description: Final[Optional[PropertyDescription]]

    #: The original class where this property is specified.
    #: We stack all the properties over the ancestors, so using ``specified_for``
    #: you can distinguish between inherited properties and genuine properties of
    #: a class.
    specified_for: Final["Class"]

    #: Relation to the property from the parse stage
    parsed: Final[parse.Property]

    def __init__(
        self,
        name: Identifier,
        type_annotation: TypeAnnotationUnion,
        description: Optional[PropertyDescription],
        specified_for: "Class",
        parsed: parse.Property,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.type_annotation = type_annotation
        self.description = description
        self.specified_for = specified_for
        self.parsed = parsed

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class DefaultConstant:
    """Represent a constant value as a default for an argument."""

    #: The default value
    value: Final[Union[bool, int, float, str, None]]

    #: Relation to the parsed stage
    parsed: Final[parse.Default]

    def __init__(
        self, value: Union[bool, int, float, str, None], parsed: parse.Default
    ) -> None:
        """Initialize with the given values."""
        self.value = value
        self.parsed = parsed


class DefaultEnumerationLiteral:
    """Represent an enumeration literal as a default for an argument."""

    #: Related enumeration
    enumeration: Final["Enumeration"]

    #: Related enumeration literal
    literal: Final["EnumerationLiteral"]

    #: Relation to the parse stage
    parsed: Final[parse.Default]

    # fmt: off
    @require(
        lambda enumeration, literal:
        literal.name in enumeration.literals_by_name
        and enumeration.literals_by_name[literal.name] == literal
    )
    # fmt: on
    def __init__(
        self,
        enumeration: "Enumeration",
        literal: "EnumerationLiteral",
        parsed: parse.Default,
    ) -> None:
        """Initialize with the given values."""
        self.parsed = parsed
        self.enumeration = enumeration
        self.literal = literal


Default = Union[DefaultConstant, DefaultEnumerationLiteral]


class Argument:
    """Represent an argument of a method (both of an interface and of class)."""

    #: Name of the argument
    name: Final[Identifier]

    #: Type annotation of the argument
    type_annotation: Final[TypeAnnotationUnion]

    #: Default value of the argument, if any
    default: Final[Optional[Default]]

    #: Relation to the parse stage
    parsed: Final[parse.Argument]

    def __init__(
        self,
        name: Identifier,
        type_annotation: TypeAnnotationUnion,
        default: Optional[Default],
        parsed: parse.Argument,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.type_annotation = type_annotation
        self.default = default
        self.parsed = parsed


class Serialization:
    """Specify the general settings for serialization of an interface or a class."""

    def __init__(self, with_model_type: bool) -> None:
        """
        Initialize with the given values.

        :param with_model_type:
            if set, the serialization needs to include a discriminator.
        """
        self.with_model_type = with_model_type


class ReferenceInTheBook:
    """Represent the information indicated in the ``reference_in_the_book`` marker."""

    #: Section number
    section: Final[Tuple[int, ...]]

    #: Index in the section so that the classes can be sorted deterministically
    index: Final[int]

    #: URL Fragment of the section
    #:
    #: The literal ``#`` needs to be prepended and the fragment needs to be URL-encoded.
    fragment: Final[Optional[str]]

    def __init__(
        self, section: Tuple[int, ...], index: int, fragment: Optional[str]
    ) -> None:
        """Initialize with the given values."""
        self.section = section
        self.index = index
        self.fragment = fragment


class Invariant:
    """Represent an invariant of a class."""

    #: Human-readable description of the invariant, if any
    description: Final[Optional[str]]

    #: Understood body of the invariant
    body: Final[parse_tree.Expression]

    #: The original symbol where this invariant is specified.
    #: We stack all the invariants over the ancestors, so using ``specified_for``
    #: you can distinguish between inherited invariants and genuine invariants of
    #: a class or a constrained primitive.
    specified_for: Final[Union["ConstrainedPrimitive", "Class"]]

    #: Relation to the parse stage
    parsed: Final[parse.Invariant]

    def __init__(
        self,
        description: Optional[str],
        body: parse_tree.Expression,
        specified_for: Union["ConstrainedPrimitive", "Class"],
        parsed: parse.Invariant,
    ) -> None:
        self.description = description
        self.body = body
        self.specified_for = specified_for
        self.parsed = parsed


class Contract:
    """Represent a contract of a method."""

    #: Argument names of the contract
    args: Final[Sequence[Identifier]]

    #: Human-readable description of the contract, if any
    description: Final[Optional[str]]

    #: Understood body of the contract
    body: Final[parse_tree.Node]

    #: Relation to the parse stage
    parsed: Final[parse.Contract]

    def __init__(
        self,
        args: Sequence[Identifier],
        description: Optional[str],
        body: parse_tree.Node,
        parsed: parse.Contract,
    ) -> None:
        """Initialize with the given values."""
        self.args = args
        self.description = description
        self.body = body
        self.parsed = parsed


class Snapshot:
    """Represent a snapshot of an OLD value capture before the method execution."""

    #: Argument names of the snapshot
    args: Final[Sequence[Identifier]]

    #: Understood body of the snapshot
    body: Final[parse_tree.Node]

    #: Name of the snapshot variable
    name: Final[Identifier]

    #: Relation to parse stage
    parsed: Final[parse.Snapshot]

    def __init__(
        self,
        args: Sequence[Identifier],
        body: parse_tree.Node,
        name: Identifier,
        parsed: parse.Snapshot,
    ) -> None:
        """Initialize with the given values."""
        self.args = args
        self.body = body
        self.name = name
        self.parsed = parsed


class Contracts:
    """Represent the set of contracts for a method or a function."""

    # NOTE (mristin, 2022-04-07):
    # Common programming languages which work with contracts usually implement
    # pre-conditions in a disjunctive normal form, *i.e.* as a disjunction of
    # conjunctions, where at least one conjunction needs to hold. The individual
    # conjunctions correspond to the levels of the inheritance hierarchy.
    #
    # However, we have not touched methods at the moment nor their proper inheritance.
    # Therefore we leave the pre-conditions in the intermediate representation as they
    # would appear in the code, without inheritance and hence without disjunctions.
    # In the future, once we want to tackle the methods as a feature, we need to change
    # the way how we model and resolve the pre-conditions through
    # the inheritance hierarchy.

    #: Pre-conditions that need to hold *before* the call
    preconditions: Final[Sequence[Contract]]

    #: Snapshots which are captured *before* the call
    snapshots: Final[Sequence[Snapshot]]

    #: Post-conditions that need to hold *after* the call
    postconditions: Final[Sequence[Contract]]

    def __init__(
        self,
        preconditions: Sequence[Contract],
        snapshots: Sequence[Snapshot],
        postconditions: Sequence[Contract],
    ) -> None:
        """Initialize with the given values."""
        self.preconditions = preconditions
        self.snapshots = snapshots
        self.postconditions = postconditions


class SignatureLike(DBC):
    """
    Represent a signature-like "something".

    This can be either a signature of a method, a method or a function.
    """

    #: Name of the signature-like
    name: Final[Identifier]

    #: Arguments of the signature-like
    arguments: Final[Sequence[Argument]]

    #: Return type of the signature-like
    returns: Final[Optional[TypeAnnotationUnion]]

    #: Description of the signature-like, if any
    description: Final[Optional[SignatureDescription]]

    #: List of contracts of the signature-like. The contracts are stacked from the
    #: ancestors.
    contracts: Final[Contracts]

    # NOTE (mristin, 2021-12-26):
    # The ``parsed`` must be optional since constructors can be synthesized without
    # being defined in the original meta-model.

    #: Relation to the parse stage
    parsed: Optional[parse.Method]

    #: Map arguments by their names
    arguments_by_name: Final[Mapping[Identifier, Argument]]

    # fmt: off
    @require(
        lambda arguments:
        all(
            arg.name != 'self'
            for arg in arguments
        ),
        "No explicit ``self`` argument in the arguments"
    )
    @require(
        lambda arguments: (
                arg_names := [arg.name for arg in arguments],
                len(arg_names) == len(set(arg_names))
        )[1],
        "Unique arguments"
    )
    @ensure(
        lambda self:
        len(self.arguments) == len(self.arguments_by_name)
        and all(
            (
                    found_argument := self.arguments_by_name.get(argument.name, None),
                    found_argument is not None and found_argument is argument
            )[1]
            for argument in self.arguments
        ),
        "Arguments and arguments-by-name consistent"
    )
    # fmt: on
    def __init__(
        self,
        name: Identifier,
        arguments: Sequence[Argument],
        returns: Optional[TypeAnnotationUnion],
        description: Optional[SignatureDescription],
        contracts: Contracts,
        parsed: Optional[parse.Method],
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.arguments = arguments
        self.returns = returns
        self.description = description
        self.contracts = contracts
        self.parsed = parsed

        self.arguments_by_name = {
            argument.name: argument for argument in self.arguments
        }

    @abc.abstractmethod
    def __repr__(self) -> str:
        # Signal that this is a pure abstract class
        raise NotImplementedError()


class Method(SignatureLike):
    """Represent a method of a class."""

    # NOTE (mristin, 2021-12-26):
    # The ``parsed`` must be optional in the parent class, ``SignatureLike``, since
    # constructors can be synthesized without being defined in the original meta-model.
    #
    # However, methods are never synthesized so we always have a clear link to the parse
    # stage.

    parsed: parse.Method

    #: The original class where this method is specified.
    #: We stack all the methods over the ancestors, so using ``specified_for``
    #: you can distinguish between inherited methods and genuine methods of
    #: a class.
    specified_for: Final["Class"]

    # fmt: off
    @require(
        lambda name:
        name != "__init__",
        "Expected constructors to be handled in a special way and not as a method"
    )
    @require(
        lambda arguments, contracts:
        (
                arg_set := {arg.name for arg in arguments},
                all(
                    arg in arg_set  # pylint: disable=used-before-assignment
                    for precondition in contracts.preconditions
                    for arg in precondition.args
                    if arg != 'self'
                )
                and all(
                    arg in arg_set
                    for postcondition in contracts.postconditions
                    for arg in postcondition.args
                    if arg not in ('OLD', 'result', 'self')
                )
                and all(
                    arg in arg_set
                    for snapshot in contracts.snapshots
                    for arg in snapshot.args
                    if arg.name != 'self'
                )
        )[1],
        "All arguments of contracts defined in method arguments except ``self``"
    )
    # fmt: on
    def __init__(
        self,
        name: Identifier,
        arguments: Sequence[Argument],
        returns: Optional[TypeAnnotationUnion],
        description: Optional[SignatureDescription],
        specified_for: "Class",
        contracts: Contracts,
        parsed: parse.Method,
    ) -> None:
        """Initialize with the given values."""
        SignatureLike.__init__(
            self,
            name=name,
            arguments=arguments,
            returns=returns,
            description=description,
            contracts=contracts,
            parsed=parsed,
        )

        self.specified_for = specified_for

    @abc.abstractmethod
    def __repr__(self) -> str:
        # Signal that this is a pure abstract class.
        raise NotImplementedError()


# NOTE (mristin, 2021-12-19):
# At the moment, we support only implementation-specific methods. However, we anticipate
# that we will try to understand the methods in the very near future so we already
# prepare the class hierarchy for it.


class ImplementationSpecificMethod(Method):
    """Represent an implementation-specific method of a class."""

    # NOTE (mristin, 2021-12-26):
    # The ``parsed`` must be optional in the parent class, ``SignatureLike``, since
    # constructors can be synthesized without being defined in the original meta-model.
    #
    # However, methods are never synthesized so we always have a clear link to the parse
    # stage here.

    #: Relation to parse stage
    parsed: parse.Method

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class UnderstoodMethod(Method):
    """Represent a method of a class which we could understand."""

    #: Understood syntax tree of the method's body
    body: Final[Sequence[parse_tree.Node]]

    # NOTE (mristin, 2021-12-26):
    # The ``parsed`` must be optional in the parent class, ``SignatureLike``, since
    # constructors can be synthesized without being defined in the original meta-model.
    #
    # However, methods are never synthesized so we always have a clear link to the parse
    # stage here.

    #: Relation to parse stage
    parsed: parse.Method

    def __init__(
        self,
        name: Identifier,
        arguments: Sequence[Argument],
        returns: Optional[TypeAnnotationUnion],
        description: Optional[SignatureDescription],
        specified_for: "Class",
        contracts: Contracts,
        body: Sequence[parse_tree.Node],
        parsed: parse.Method,
    ) -> None:
        """Initialize with the given values."""
        Method.__init__(
            self,
            name=name,
            arguments=arguments,
            returns=returns,
            description=description,
            specified_for=specified_for,
            contracts=contracts,
            parsed=parsed,
        )

        self.body = body

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class Constructor(SignatureLike):
    """
    Represent an understood constructor of a class stacked.

    The constructor is expected to be stacked from the class and all the ancestors.
    """

    #: Interpreted statements of the constructor, stacked over all the ancestors
    statements: Final[Sequence[construction.AssignArgument]]

    #: If set, the constructor is implementation-specific and we need to provide
    #: a snippet for it.
    is_implementation_specific: Final[bool]

    def __init__(
        self,
        is_implementation_specific: bool,
        arguments: Sequence[Argument],
        contracts: Contracts,
        description: Optional[SignatureDescription],
        statements: Sequence[construction.AssignArgument],
        parsed: Optional[parse.Method],
    ) -> None:
        SignatureLike.__init__(
            self,
            name=Identifier("__init__"),
            arguments=arguments,
            returns=None,
            description=description,
            contracts=contracts,
            parsed=parsed,
        )

        self.is_implementation_specific = is_implementation_specific

        # The calls to the super constructors must be in-lined before.
        self.statements = statements

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return f"<{_MODULE_NAME}.{self.__class__.__name__} at 0x{id(self):x}>"


class EnumerationLiteral:
    """Represent a single enumeration literal."""

    def __init__(
        self,
        name: Identifier,
        value: str,
        description: Optional[EnumerationLiteralDescription],
        parsed: parse.EnumerationLiteral,
    ) -> None:
        self.name = name
        self.value = value
        self.description = description
        self.parsed = parsed


# fmt: off
@invariant(
    lambda self:
    all(
        literal == self.literals_by_name[literal.name]
        for literal in self.literals
    ),
    "Literal map consistent on name"
)
@invariant(
    lambda self:
    sorted(map(id, self.literals_by_name.values())) == sorted(map(id, self.literals)),
    "Literal map complete"
)
# fmt: on
class Enumeration:
    """Represent an enumeration."""

    #: Name of the enumeration
    name: Final[Identifier]

    #: Literals associated with the enumeration
    literals: Final[Sequence[EnumerationLiteral]]

    #: List which enumerations *this* enumeration is a superset of;
    #: this is akin to inheritance for enumerations
    is_superset_of: Final[Sequence["Enumeration"]]

    #: Reference to the original specs
    reference_in_the_book: Final[Optional[ReferenceInTheBook]]

    #: Description of the enumeration, if any
    description: Final[Optional[SymbolDescription]]

    #: Map literals by their identifiers
    literals_by_name: Final[Mapping[str, EnumerationLiteral]]

    #: Collect IDs (with :py:func:`id`) of the literal objects in a set
    literal_id_set: Final[FrozenSet[int]]

    def __init__(
        self,
        name: Identifier,
        literals: Sequence[EnumerationLiteral],
        is_superset_of: Sequence["Enumeration"],
        reference_in_the_book: Optional[ReferenceInTheBook],
        description: Optional[SymbolDescription],
        parsed: parse.Enumeration,
    ) -> None:
        self.name = name
        self.literals = literals
        self.is_superset_of = is_superset_of
        self.reference_in_the_book = reference_in_the_book
        self.description = description
        self.parsed = parsed

        self.literals_by_name: Mapping[str, EnumerationLiteral] = {
            literal.name: literal for literal in self.literals
        }

        self.literal_id_set = frozenset(id(literal) for literal in literals)

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class ConstrainedPrimitive:
    """Represent a primitive type constrained by one or more invariants."""

    #: Name of the class
    name: Final[Identifier]

    # region Inheritances

    # NOTE (mristin, 2021-12-24):
    # We have to decorate inheritances with ``@property`` so that the client code is
    # forced to use ``_set_inheritances``.

    _inheritances: Sequence["ConstrainedPrimitive"]

    @property
    def inheritances(self) -> Sequence["ConstrainedPrimitive"]:
        """Return direct parents that this class inherits from."""
        return self._inheritances

    _inheritance_id_set: FrozenSet[int]

    @property
    def inheritance_id_set(self) -> FrozenSet[int]:
        """Collect IDs (with :py:func:`id`) of the inheritance objects in a set."""
        return self._inheritance_id_set

    # endregion

    # region Descendants

    # NOTE (mristin, 2021-12-24):
    # We have to decorate ``descendant_id_set`` with
    # ``@property`` so that the translation code is forced to use
    # ``_set_descendants``.

    _descendant_id_set: FrozenSet[int]

    @property
    def descendant_id_set(self) -> FrozenSet[int]:
        """List the IDs (as in Python's ``id`` built-in) of the descendants."""
        return self._descendant_id_set

    # endregion

    #: Which primitive type is constrained
    constrainee: PrimitiveType

    #: If set, this class is implementation-specific and we need to provide a snippet
    #: for each implementation target
    is_implementation_specific: Final[bool]

    # region Invariants

    # NOTE (mristin, 2022-03-19):
    # We have to decorate invariants with ``@property`` so that the translation code
    # is forced to use ``_set_invariants``.

    _invariants: Sequence[Invariant]

    @property
    def invariants(self) -> Sequence[Invariant]:
        """List invariants of the class."""
        return self._invariants

    _invariant_id_set: FrozenSet[int]

    @property
    def invariant_id_set(self) -> FrozenSet[int]:
        """Collect IDs (with :py:func:`id`) of the invariant objects in a set."""
        return self._invariant_id_set

    # endregion

    #: Reference to the original specs
    reference_in_the_book: Final[Optional[ReferenceInTheBook]]

    #: Description of the class
    description: Final[Optional[SymbolDescription]]

    #: Relation to the class from the parse stage
    parsed: parse.Class

    # fmt: off
    @require(
        lambda parsed: len(parsed.methods) == 0,
        "No methods expected in the constrained primitive type"
    )
    @require(
        lambda parsed: len(parsed.properties) == 0,
        "No properties expected in the constrained primitive type"
    )
    @require(
        lambda constrainee, inheritances:
        all(
            inheritance.constrainee == constrainee
            for inheritance in inheritances
        ),
        "Constrainee consistent with ancestors"
    )
    @require(
        lambda constrainee, descendants:
        all(
            descendant.constrainee == constrainee
            for descendant in descendants
        ),
        "Constrainee consistent with descendants"
    )
    # fmt: on
    def __init__(
        self,
        name: Identifier,
        inheritances: Sequence["ConstrainedPrimitive"],
        descendants: Sequence["ConstrainedPrimitive"],
        constrainee: PrimitiveType,
        is_implementation_specific: bool,
        invariants: Sequence[Invariant],
        reference_in_the_book: Optional[ReferenceInTheBook],
        description: Optional[SymbolDescription],
        parsed: parse.Class,
    ) -> None:
        self.name = name
        self._set_inheritances(inheritances)
        self._set_descendants(descendants)
        self.constrainee = constrainee
        self.is_implementation_specific = is_implementation_specific
        self._set_invariants(invariants)
        self.reference_in_the_book = reference_in_the_book
        self.description = description
        self.parsed = parsed

    @require(lambda self, descendants: self not in descendants)
    def _set_descendants(self, descendants: Sequence["ConstrainedPrimitive"]) -> None:
        """
        Set the descendants in the constrained primitive.

        This method is expected to be called only during the translation phase.
        """
        self._descendant_id_set = frozenset(
            id(descendant) for descendant in descendants
        )

    def _set_invariants(self, invariants: Sequence[Invariant]) -> None:
        """
        Set the invariants in the class.

        This method is expected to be called only during the translation phase.
        """
        self._invariants = invariants
        self._invariant_id_set = frozenset(id(invariant) for invariant in invariants)

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )

    # fmt: off
    @require(
        lambda inheritances:
        len(inheritances) == len(set(inheritance.name for inheritance in inheritances)),
        "No duplicate inheritances"
    )
    # fmt: on
    def _set_inheritances(self, inheritances: Sequence["ConstrainedPrimitive"]) -> None:
        """
        Set the inheritances in the class.

        This method is expected to be called only during the translation phase.
        """
        self._inheritances = inheritances

        self._inheritance_id_set = frozenset(
            id(inheritance) for inheritance in self._inheritances
        )


class Class(DBC):
    """Represent an abstract or a concrete class."""

    #: Name of the class
    name: Final[Identifier]

    # region Inheritances

    # NOTE (mristin, 2021-12-24):
    # We have to decorate inheritances with ``@property`` so that the translation code
    # is forced to use ``_set_inheritances``.

    _inheritances: Sequence["ClassUnion"]

    @property
    def inheritances(self) -> Sequence["ClassUnion"]:
        """Return direct parents that this class inherits from."""
        return self._inheritances

    _inheritance_id_set: FrozenSet[int]

    @property
    def inheritance_id_set(self) -> FrozenSet[int]:
        """Collect IDs (with :py:func:`id`) of the inheritance objects in a set."""
        return self._inheritance_id_set

    def is_subclass_of(self, cls: "ClassUnion") -> bool:
        """
        Check recursively whether this class is a sub-class of ``cls``.

        Every class is a sub-class of itself.
        """
        # NOTE (mristin, 2022-05-13):
        # This function is not used by the aas-core-codegen, but by downstream clients
        # such as aas-core3.0rc02-testgen.

        if id(cls) == id(self):
            return True

        queue = [self]  # type: List[Class]
        while len(queue) > 0:
            top = queue.pop()
            if id(cls) in top.inheritance_id_set:
                return True

            queue.extend(top.inheritances)

        return False

    # endregion

    #: If set, this class is implementation-specific and we need to provide a snippet
    #: for each implementation target
    is_implementation_specific: Final[bool]

    #: Interface of the class. If it is a concrete class with no descendants, there is
    #: no interface available.
    interface: Optional["Interface"]

    # region Descendants

    # NOTE (mristin, 2021-12-24):
    # We have to decorate ``descendant_id_set`` and ``concrete_descendants`` with
    # ``@property`` so that the translation code is forced to use
    # ``_set_descendants``.

    _descendant_id_set: FrozenSet[int]

    _concrete_descendants: Sequence["ConcreteClass"]

    @property
    def descendant_id_set(self) -> FrozenSet[int]:
        """List the IDs (as in Python's ``id`` built-in) of the descendants."""
        return self._descendant_id_set

    @property
    def concrete_descendants(self) -> Sequence["ConcreteClass"]:
        """List descendants of this class which are concrete classes."""
        return self._concrete_descendants

    # endregion

    # region Properties

    # NOTE (mristin, 2022-03-19):
    # We have to decorate properties with ``@property`` so that the translation code
    # is forced to use ``_set_properties``.

    _properties: Sequence[Property]

    @property
    def properties(self) -> Sequence[Property]:
        """Return list of properties of the class."""
        return self._properties

    _properties_by_name: Mapping[Identifier, Property]

    @property
    def properties_by_name(self) -> Mapping[Identifier, Property]:
        """Map all properties by their names."""
        return self._properties_by_name

    _property_id_set: FrozenSet[int]

    @property
    def property_id_set(self) -> FrozenSet[int]:
        """Collect IDs (with :py:func:`id`) of the property objects in a set."""
        return self._property_id_set

    # endregion

    # region Methods

    # NOTE (mristin, 2022-03-19):
    # We have to decorate methods with ``@property`` so that the translation code
    # is forced to use ``_set_methods``.

    _methods: Sequence["MethodUnion"]

    @property
    def methods(self) -> Sequence["MethodUnion"]:
        """
        List methods of the class.

        The methods are strictly non-static and non-class (in the Python sense of
        the terms).
        """
        return self._methods

    _methods_by_name: Mapping[Identifier, "MethodUnion"]

    @property
    def methods_by_name(self) -> Mapping[Identifier, "MethodUnion"]:
        """Map all methods by their names."""
        return self._methods_by_name

    # endregion

    #: Constructor specification of the class
    constructor: Final[Constructor]

    # region Invariants

    # NOTE (mristin, 2022-03-19):
    # We have to decorate invariants with ``@property`` so that the translation code
    # is forced to use ``_set_invariants``.

    _invariants: Sequence[Invariant]

    @property
    def invariants(self) -> Sequence[Invariant]:
        """List invariants of the class."""
        return self._invariants

    _invariant_id_set: FrozenSet[int]

    @property
    def invariant_id_set(self) -> FrozenSet[int]:
        """Collect IDs (with :py:func:`id`) of the invariant objects in a set."""
        return self._invariant_id_set

    # endregion

    #: Particular serialization settings for this class
    serialization: Final[Serialization]

    #: Reference to the original specs
    reference_in_the_book: Final[Optional[ReferenceInTheBook]]

    #: Description of the class
    description: Final[Optional[SymbolDescription]]

    #: Relation to the class from the parse stage
    parsed: Final[parse.Class]

    def __init__(
        self,
        name: Identifier,
        inheritances: Sequence["ClassUnion"],
        interface: Optional["Interface"],
        descendants: Sequence["ClassUnion"],
        is_implementation_specific: bool,
        properties: Sequence[Property],
        methods: Sequence["MethodUnion"],
        constructor: Constructor,
        invariants: Sequence[Invariant],
        serialization: Serialization,
        reference_in_the_book: Optional[ReferenceInTheBook],
        description: Optional[SymbolDescription],
        parsed: parse.Class,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self._set_inheritances(inheritances)
        self.interface = interface
        self._set_descendants(descendants)
        self.is_implementation_specific = is_implementation_specific
        self._set_properties(properties)
        self._set_methods(methods)
        self.constructor = constructor
        self._set_invariants(invariants)
        self.serialization = serialization
        self.reference_in_the_book = reference_in_the_book
        self.description = description
        self.parsed = parsed

    # fmt: off
    @require(
        lambda inheritances:
        len(inheritances) == len(set(inheritance.name for inheritance in inheritances)),
        "No duplicate inheritances"
    )
    # fmt: on
    def _set_inheritances(self, inheritances: Sequence["ClassUnion"]) -> None:
        """
        Set the inheritances in the class.

        This method is expected to be called only during the translation phase.
        """
        self._inheritances = inheritances

        self._inheritance_id_set = frozenset(
            id(inheritance) for inheritance in self._inheritances
        )

    @require(lambda self, descendants: self not in descendants)
    def _set_descendants(self, descendants: Sequence["ClassUnion"]) -> None:
        """
        Set the descendants and the concrete descendants in the class.

        This method is expected to be called only during the translation phase.
        """
        self._descendant_id_set = frozenset(
            id(descendant) for descendant in descendants
        )

        self._concrete_descendants = [
            descendant
            for descendant in descendants
            if isinstance(descendant, ConcreteClass)
        ]

    # fmt: off
    @require(
        lambda properties:
        len(properties) == len(set(prop.name for prop in properties)),
        "No duplicate properties"
    )
    # fmt: on
    def _set_properties(self, properties: Sequence[Property]) -> None:
        """
        Set the properties in the class.

        This method is expected to be called only during the translation phase.
        """
        self._properties = properties
        self._properties_by_name = {prop.name: prop for prop in properties}
        self._property_id_set = frozenset(id(prop) for prop in properties)

    # fmt: off
    @require(
        lambda methods:
        len(methods) == len(set(method.name for method in methods)),
        "No duplicate methods"
    )
    # fmt: on
    def _set_methods(self, methods: Sequence["MethodUnion"]) -> None:
        """
        Set the methods in the class.

        This method is expected to be called only during the translation phase.
        """
        self._methods = methods
        self._methods_by_name = {method.name: method for method in methods}

    def _set_invariants(self, invariants: Sequence[Invariant]) -> None:
        """
        Set the invariants in the class.

        This method is expected to be called only during the translation phase.
        """
        self._invariants = invariants
        self._invariant_id_set = frozenset(id(invariant) for invariant in invariants)

    @abc.abstractmethod
    def __repr__(self) -> str:
        # Signal that this is a purely abstract class.
        raise NotImplementedError()


class ConcreteClass(Class):
    """Represent a class that can be instantiated."""

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class AbstractClass(Class):
    """Represent a class that is purely abstract and can not be instantiated."""

    #: Interface of the class. All abstract classes have an interface as opposed to
    #: concrete classes, which only have an interface if there are descendants.
    interface: "Interface"

    # We need to override the constructor because the ``interface`` is required.
    def __init__(
        self,
        name: Identifier,
        inheritances: Sequence["ClassUnion"],
        interface: "Interface",
        descendants: Sequence["ClassUnion"],
        is_implementation_specific: bool,
        properties: Sequence[Property],
        methods: Sequence["MethodUnion"],
        constructor: Constructor,
        invariants: Sequence[Invariant],
        serialization: Serialization,
        reference_in_the_book: Optional[ReferenceInTheBook],
        description: Optional[SymbolDescription],
        parsed: parse.Class,
    ) -> None:
        """Initialize with the given values."""
        Class.__init__(
            self,
            name=name,
            inheritances=inheritances,
            interface=interface,
            descendants=descendants,
            is_implementation_specific=is_implementation_specific,
            properties=properties,
            methods=methods,
            constructor=constructor,
            invariants=invariants,
            serialization=serialization,
            reference_in_the_book=reference_in_the_book,
            description=description,
            parsed=parsed,
        )

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class Verification(SignatureLike):
    """Represent a verification function defined in the meta-model."""

    parsed: parse.Method

    # fmt: off
    @require(
        lambda arguments, contracts:
        (
                arg_set := {arg.name for arg in arguments},
                all(
                    arg in arg_set  # pylint: disable=used-before-assignment
                    for precondition in contracts.preconditions
                    for arg in precondition.args
                )
                and all(
                    arg in arg_set
                    for postcondition in contracts.postconditions
                    for arg in postcondition.args
                    if arg not in ('OLD', 'result')
                )
                and all(
                    arg in arg_set
                    for snapshot in contracts.snapshots
                    for arg in snapshot.args
                )
        )[1],
        "All arguments of contracts defined in function arguments"
    )
    # fmt: on
    def __init__(
        self,
        name: Identifier,
        arguments: Sequence[Argument],
        returns: Optional[TypeAnnotationUnion],
        description: Optional[SignatureDescription],
        contracts: Contracts,
        parsed: parse.Method,
    ) -> None:
        """Initialize with the given values."""
        SignatureLike.__init__(
            self,
            name=name,
            arguments=arguments,
            returns=returns,
            description=description,
            contracts=contracts,
            parsed=parsed,
        )

    @abc.abstractmethod
    def __repr__(self) -> str:
        # Signal that this is a pure abstract class.
        raise NotImplementedError()


class ImplementationSpecificVerification(Verification):
    """Represent an implementation-specific verification function."""

    def __init__(
        self,
        name: Identifier,
        arguments: Sequence[Argument],
        returns: Optional[TypeAnnotationUnion],
        description: Optional[SignatureDescription],
        contracts: Contracts,
        parsed: parse.Method,
    ) -> None:
        """Initialize with the given values."""
        Verification.__init__(
            self,
            name=name,
            arguments=arguments,
            returns=returns,
            description=description,
            contracts=contracts,
            parsed=parsed,
        )

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class PatternVerification(Verification):
    """
    Represent a function that checks a string against a regular expression.

    There is expected to be a single string argument (the text to be matched).
    The function is expected to return a boolean.
    """

    #: Method as we understood it in the parse stage
    parsed: parse.UnderstoodMethod

    #: Pattern, *i.e.* the regular expression, that the function checks against
    pattern: Final[str]

    # fmt: off
    @require(
        lambda arguments:
        len(arguments) == 1
        and isinstance(arguments[0].type_annotation, PrimitiveTypeAnnotation)
        and arguments[0].type_annotation.a_type == PrimitiveType.STR,
        "There is a single string argument"
    )
    @require(
        lambda returns:
        (returns is not None)
        and isinstance(returns, PrimitiveTypeAnnotation)
        and returns.a_type == PrimitiveType.BOOL
    )
    # fmt: on
    def __init__(
        self,
        name: Identifier,
        arguments: Sequence[Argument],
        returns: Optional[TypeAnnotationUnion],
        description: Optional[SignatureDescription],
        contracts: Contracts,
        pattern: str,
        parsed: parse.UnderstoodMethod,
    ) -> None:
        """Initialize with the given values."""
        Verification.__init__(
            self,
            name=name,
            arguments=arguments,
            returns=returns,
            description=description,
            contracts=contracts,
            parsed=parsed,
        )

        self.pattern = pattern

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class Signature(SignatureLike):
    """Represent a signature of a method in an interface."""

    def __init__(
        self,
        name: Identifier,
        arguments: Sequence[Argument],
        returns: Optional[TypeAnnotationUnion],
        description: Optional[SignatureDescription],
        contracts: Contracts,
        parsed: parse.Method,
    ) -> None:
        """
        Initialize with the given values.

        The ``parsed`` refers to the method of the abstract or concrete class that
        defines the interface. Mind that we do not introduce interfaces as a concept
        in the meta-model.
        """
        SignatureLike.__init__(
            self,
            name=name,
            arguments=arguments,
            returns=returns,
            description=description,
            contracts=contracts,
            parsed=parsed,
        )

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class Interface:
    """
    Represent an interface of some of the abstract and/or concrete classes.

    Mind that the concept of interfaces is *not* used in the meta-model. We introduce
    it at the intermediate stage to facilitate generation of the code, especially for
    targets where multiple inheritance is not supported.
    """

    #: Class which this interface is based on
    base: Final[Class]

    #: Name of the interface
    name: Final[Identifier]

    inheritances: Final[Sequence["Interface"]]

    #: List of concrete classes that implement this interface
    implementers: Sequence["ConcreteClass"]

    #: List of properties assumed by the interface
    properties: Final[Sequence[Property]]

    #: List of method signatures assumed by the interface
    signatures: Final[Sequence[Signature]]

    #: Description of the interface, taken from class
    description: Final[Optional[SymbolDescription]]

    #: Relation to the class from the parse stage
    parsed: Final[parse.Class]

    #: Map all properties by their identifiers to the corresponding objects
    properties_by_name: Final[Mapping[Identifier, Property]]

    #: Collect IDs (with :py:func:`id`) of the property objects in a set
    property_id_set: Final[FrozenSet[int]]

    def __init__(
        self,
        base: Class,
        inheritances: Sequence["Interface"],
    ) -> None:
        """Initialize with the given values."""
        self.base = base

        self.name = base.name
        self.inheritances = inheritances

        implementers = list(base.concrete_descendants)

        if isinstance(base, ConcreteClass):
            implementers.append(base)

        self.implementers = implementers

        self.properties = base.properties

        self.signatures = [
            Signature(
                name=method.name,
                arguments=method.arguments,
                returns=method.returns,
                description=method.description,
                contracts=method.contracts,
                parsed=method.parsed,
            )
            for method in base.methods
            if method.specified_for is base
        ]

        self.description = base.description
        self.parsed = base.parsed

        self.properties_by_name: Mapping[Identifier, Property] = {
            prop.name: prop for prop in self.properties
        }

        self.property_id_set = frozenset(id(prop) for prop in self.properties)

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


T = TypeVar("T")


class MetaModel:
    """Collect information about the underlying meta-model."""

    #: Description of the meta-model extracted from the docstring
    description: Final[Optional[MetaModelDescription]]

    #: Specify the URL of the book that the meta-model is based on
    book_url: Final[str]

    #: Specify the version of the book that the meta-model is based on
    book_version: Final[str]

    def __init__(
        self,
        book_url: str,
        book_version: str,
        description: Optional[MetaModelDescription],
    ) -> None:
        self.book_url = book_url
        self.book_version = book_version
        self.description = description


class SymbolTable:
    """Represent all the symbols of the intermediate representation."""

    #: List of all symbols that we need for the code generation
    symbols: Final[Sequence["Symbol"]]

    #: List of all the symbols, topologically sorted by inheritance
    symbols_topologically_sorted: Final[Sequence["Symbol"]]

    #: List of all functions used in the verification
    verification_functions: Final[Sequence["VerificationUnion"]]

    #: Map verification functions by their name
    verification_functions_by_name: Final[Mapping[Identifier, "VerificationUnion"]]

    #: Additional information about the source meta-model
    meta_model: Final[MetaModel]

    _name_to_symbol: Final[Mapping[Identifier, "Symbol"]]

    # fmt: off
    @require(
        lambda symbols: (
                names := [symbol.name for symbol in symbols],
                len(names) == len(set(names)),
        )[1],
        "Symbol names unique",
    )
    @require(
        lambda symbols, symbols_topologically_sorted:
        set(
            id(symbol)
            for symbol in symbols
            if not isinstance(symbol, Enumeration)
        )
        == set(id(symbol) for symbol in symbols_topologically_sorted),
        "Only maybe the order differs between the symbols and "
        "symbols_topologically_sorted"
    )
    @ensure(
        lambda self:
        all(
            self.verification_functions_by_name[func.name] is func
            for func in self.verification_functions
        )
        and len(self.verification_functions_by_name) == len(
            self.verification_functions),
        "The verification functions and their mapping by name are consistent"
    )
    @ensure(
        lambda self:
        all(
            (
                    found_symbol := self.find(symbol.name),
                    found_symbol is not None and found_symbol is symbol
            )[1]
            for symbol in self.symbols
        ),
        "Finding symbols is consistent with ``symbols``"
    )
    # fmt: on
    def __init__(
        self,
        symbols: Sequence["Symbol"],
        symbols_topologically_sorted: Sequence["SymbolExceptEnumeration"],
        verification_functions: Sequence["VerificationUnion"],
        meta_model: MetaModel,
    ) -> None:
        """Initialize with the given values and map symbols to name."""
        self.symbols = symbols
        self.symbols_topologically_sorted = symbols_topologically_sorted
        self.verification_functions = verification_functions
        self.meta_model = meta_model

        self.verification_functions_by_name = {
            func.name: func for func in self.verification_functions
        }

        self._name_to_symbol = {symbol.name: symbol for symbol in symbols}

    def find(self, name: Identifier) -> Optional["Symbol"]:
        """Find the symbol with the given ``name``."""
        return self._name_to_symbol.get(name, None)

    def must_find(self, name: Identifier) -> "Symbol":
        """
        Find the symbol with the given ``name``.

        :raise: :py:class:`KeyError` if the ``name`` is not in the table.
        """
        result = self.find(name)
        if result is None:
            raise KeyError(
                f"Could not find the symbol with the name {name} "
                f"in the symbol table"
            )

        return result


def map_descendability(
    type_annotation: TypeAnnotationUnion,
) -> MutableMapping[TypeAnnotationUnion, bool]:
    """
    Map the type annotation recursively by the descendability.

    The descendability means that the type annotation references an interface
    or a class *or* that it is a subscripted type annotation which subscribes one or
    more classes of the meta-model.

    Constrained primitives are considered primitives and thus non-descendable.

    The mapping is a form of caching. Otherwise, the time complexity would be quadratic
    if we queried at each type annotation subscript.
    """
    mapping = dict()  # type: MutableMapping[TypeAnnotationUnion, bool]

    def recurse(a_type_annotation: TypeAnnotationUnion) -> bool:
        """Recursively iterate over subscripted type annotations."""
        if isinstance(a_type_annotation, PrimitiveTypeAnnotation):
            mapping[a_type_annotation] = False
            return False

        elif isinstance(a_type_annotation, OurTypeAnnotation):
            result = None  # type: Optional[bool]
            if isinstance(a_type_annotation.symbol, Enumeration):
                result = False
            elif isinstance(a_type_annotation.symbol, ConstrainedPrimitive):
                result = False
            elif isinstance(a_type_annotation.symbol, Class):
                result = True
            else:
                assert_never(a_type_annotation.symbol)

            assert result is not None
            mapping[a_type_annotation] = result
            return result

        elif isinstance(a_type_annotation, ListTypeAnnotation):
            result = recurse(a_type_annotation=a_type_annotation.items)
            mapping[a_type_annotation] = result
            return result

        elif isinstance(a_type_annotation, OptionalTypeAnnotation):
            result = recurse(a_type_annotation=a_type_annotation.value)
            mapping[a_type_annotation] = result
            return result

        else:
            assert_never(a_type_annotation)

        raise AssertionError("Should not have gotten here")

    _ = recurse(a_type_annotation=type_annotation)

    return mapping


class _ConstructorArgumentOfClass:
    """Represent a constructor argument with its corresponding class."""

    def __init__(self, arg: Argument, cls: Class) -> None:
        """Initialize with the given values."""
        self.arg = arg
        self.cls = cls


def collect_ids_of_symbols_in_properties(symbol_table: SymbolTable) -> Set[int]:
    """
    Collect the IDs of the symbols occurring in type annotations of the properties.

    The IDs refer to IDs of the Python objects in this context.
    """
    result = set()  # type: Set[int]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        elif isinstance(symbol, ConstrainedPrimitive):
            continue

        elif isinstance(symbol, Class):
            for prop in symbol.properties:
                type_anno = prop.type_annotation

                old_type_anno = None  # type: Optional[TypeAnnotation]
                while True:
                    if isinstance(type_anno, OptionalTypeAnnotation):
                        # noinspection PyUnresolvedReferences
                        type_anno = type_anno.value
                    elif isinstance(type_anno, ListTypeAnnotation):
                        type_anno = type_anno.items
                    elif isinstance(type_anno, PrimitiveTypeAnnotation):
                        break
                    elif isinstance(type_anno, OurTypeAnnotation):
                        result.add(id(type_anno.symbol))
                        break
                    else:
                        assert_never(type_anno)

                    assert old_type_anno is not type_anno, "Loop invariant"
                    old_type_anno = type_anno
        else:
            assert_never(symbol)

    return result


DescriptionUnion = Union[
    MetaModelDescription,
    SymbolDescription,
    PropertyDescription,
    EnumerationLiteralDescription,
    SignatureDescription,
]
assert_union_of_descendants_exhaustive(
    union=DescriptionUnion, base_class=SummaryRemarksDescription
)

ClassUnion = Union[AbstractClass, ConcreteClass]
assert_union_of_descendants_exhaustive(union=ClassUnion, base_class=Class)

MethodUnion = Union[UnderstoodMethod, ImplementationSpecificMethod]
assert_union_of_descendants_exhaustive(union=MethodUnion, base_class=Method)

Symbol = Union[Enumeration, ConstrainedPrimitive, ClassUnion]

SymbolExceptEnumeration = Union[ConstrainedPrimitive, ClassUnion]
assert_union_without_excluded(
    original_union=Symbol, subset_union=SymbolExceptEnumeration, excluded=[Enumeration]
)

VerificationUnion = Union[ImplementationSpecificVerification, PatternVerification]
assert_union_of_descendants_exhaustive(union=VerificationUnion, base_class=Verification)
