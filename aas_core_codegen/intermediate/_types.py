"""Provide types of the intermediate representation."""
import ast
import collections
import enum
import pathlib
from typing import (
    Sequence,
    Optional,
    Union,
    TypeVar,
    Mapping,
    MutableMapping,
    List,
    Tuple,
    Set,
    Final,
    FrozenSet, OrderedDict,
)

import docutils.nodes
from icontract import require, invariant, ensure

from aas_core_codegen import parse
from aas_core_codegen.parse import (
    tree as parse_tree
)
from aas_core_codegen.common import Identifier, assert_never, Error
from aas_core_codegen.intermediate import construction

_MODULE_NAME = pathlib.Path(__file__).parent.name


class AtomicTypeAnnotation:
    """
    Represent an atomic non-composite type annotation.

    For example, ``Asset`` or ``int``.
    """


class BuiltinAtomicType(enum.Enum):
    """List primitive built-in types."""

    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    BYTEARRAY = "bytearray"


assert sorted(literal.value for literal in BuiltinAtomicType) == sorted(
    parse.BUILTIN_ATOMIC_TYPES
), "All built-in atomic types specified in the intermediate layer"

STR_TO_BUILTIN_ATOMIC_TYPE = {
    literal.value: literal for literal in BuiltinAtomicType
}  # type: Mapping[str, BuiltinAtomicType]


class BuiltinAtomicTypeAnnotation(AtomicTypeAnnotation):
    """Represent a built-in atomic type such as ``int``."""

    def __init__(self, a_type: BuiltinAtomicType, parsed: parse.TypeAnnotation) -> None:
        """Initialize with the given values."""
        self.a_type = a_type
        self.parsed = parsed

    def __str__(self) -> str:
        return str(self.a_type.value)


class OurAtomicTypeAnnotation(AtomicTypeAnnotation):
    """
    Represent an atomic annotation defined by a symbol in the meta-model.

     For example, ``Asset``.
    """

    def __init__(self, symbol: "Symbol", parsed: parse.TypeAnnotation) -> None:
        """Initialize with the given values."""
        self.symbol = symbol
        self.parsed = parsed

    def __str__(self) -> str:
        return self.symbol.name


class SubscriptedTypeAnnotation:
    """Represent a subscripted (i.e. composite) type annotation.

    The composite type annotations are, for example, ``List[...]`` (or
    ``Mapping[..., ...]``, *etc.*).
    """


class ListTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``List[...]``."""

    def __init__(self, items: "TypeAnnotation", parsed: parse.TypeAnnotation):
        self.items = items
        self.parsed = parsed

    def __str__(self) -> str:
        return f"List[{self.items}]"


# NOTE (mristin, 2021-11-19):
# We do not support other composite types except for ``List``. In the future we might
# add support for ``Set``, ``MutableMapping`` *etc.*


class OptionalTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving an ``Optional[...]``."""

    def __init__(self, value: "TypeAnnotation", parsed: parse.TypeAnnotation):
        self.value = value
        self.parsed = parsed

    def __str__(self) -> str:
        return f"Optional[{self.value}]"


class RefTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a reference ``Ref[...]``."""

    def __init__(self, value: "TypeAnnotation", parsed: parse.TypeAnnotation):
        self.value = value
        self.parsed = parsed


TypeAnnotation = Union[AtomicTypeAnnotation, SubscriptedTypeAnnotation]


def type_annotations_equal(that: TypeAnnotation, other: TypeAnnotation) -> bool:
    """
    Compare two type annotations for equality.

    Two type annotations are equal if they describe the same type.
    """
    if type(that) is not type(other):
        return False

    if isinstance(that, BuiltinAtomicTypeAnnotation):
        assert isinstance(other, BuiltinAtomicTypeAnnotation)
        return that.a_type == other.a_type
    elif isinstance(that, OurAtomicTypeAnnotation):
        assert isinstance(other, OurAtomicTypeAnnotation)
        return that.symbol == other.symbol
    elif isinstance(that, ListTypeAnnotation):
        assert isinstance(other, ListTypeAnnotation)
        return type_annotations_equal(that.items, other.items)
    elif isinstance(that, OptionalTypeAnnotation):
        assert isinstance(other, OptionalTypeAnnotation)
        return type_annotations_equal(that.value, other.value)
    else:
        assert_never(that)


class Description:
    """Represent a docstring describing something in the meta-model."""

    @require(lambda node: isinstance(node.value, str))
    def __init__(self, document: docutils.nodes.document, node: ast.Constant) -> None:
        """Initialize with the given values."""
        self.document = document
        self.node = node


class Property:
    """Represent a property of a class."""

    def __init__(
            self,
            name: Identifier,
            type_annotation: TypeAnnotation,
            description: Optional[Description],
            implemented_for: Optional["Symbol"],
            parsed: parse.Property,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.type_annotation = type_annotation
        self.description = description
        self.implemented_for = implemented_for
        self.parsed = parsed

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class DefaultConstant:
    """Represent a constant value as a default for an argument."""

    def __init__(
            self, value: Union[bool, int, float, str, None], parsed: parse.Default
    ) -> None:
        """Initialize with the given values."""
        self.value = value
        self.parsed = parsed


class DefaultEnumerationLiteral:
    """Represent an enumeration literal as a default for an argument."""

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

    def __init__(
            self,
            name: Identifier,
            type_annotation: TypeAnnotation,
            default: Optional[Default],
            parsed: parse.Argument,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.type_annotation = type_annotation
        self.default = default
        self.parsed = parsed


class Signature:
    """Represent a method signature."""

    def __init__(
            self,
            name: Identifier,
            arguments: Sequence[Argument],
            returns: Optional[TypeAnnotation],
            description: Optional[Description],
            parsed: parse.Method,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.arguments = arguments
        self.returns = returns
        self.description = description
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


class Interface:
    """
    Represent an interface with methods mapped to signatures.

    We also include the properties so that we can generate the getters and setters at
    a later stage.
    """

    def __init__(
            self,
            name: Identifier,
            inheritances: Sequence["Interface"],
            signatures: Sequence[Signature],
            properties: Sequence[Property],
            serialization: Serialization,
            description: Optional[Description],
            parsed: parse.Class,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.inheritances = inheritances
        self.signatures = signatures
        self.properties = properties
        self.serialization = serialization
        self.description = description
        self.parsed = parsed

        self.properties_by_name: Mapping[Identifier, Property] = {
            prop.name: prop for prop in self.properties
        }

        self.property_id_set = frozenset(id(prop) for prop in self.properties)

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class Invariant:
    """Represent an invariant of a class."""

    def __init__(
            self,
            description: Optional[str],
            body: parse_tree.Node,
            parsed: parse.Invariant) -> None:
        self.description = description
        self.body = body
        self.parsed = parsed


class Contract:
    """Represent a contract of a method."""

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
    """Represent the set of contracts for a method."""

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


class Method:
    """Represent a method of a class."""

    # fmt: off
    @require(
        lambda name:
        name != "__init__",
        "Expected constructors to be handled in a special way and not as a method"
    )
    @require(
        lambda body: not (len(body) > 0) or not parse.is_string_expr(expr=body[0]),
        "Docstring is excluded from the body"
    )
    @require(
        lambda arguments:
        all(
            arg.name != 'self'
            for arg in arguments
        ),
        "No explicit ``self`` argument in the arguments"
    )
    @require(
        lambda arguments, contracts:
        (
                arg_set := {arg.name for arg in arguments},
                all(
                    arg in arg_set  # pylint: disable=used-before-assignment
                    for precondition in contracts.preconditions
                    for arg in precondition.args
                    if arg.name != 'self'
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
    @require(
        lambda arguments: (
                arg_names := [arg.name for arg in arguments],
                len(arg_names) == len(set(arg_names))
        )[1],
        "Unique arguments"
    )
    # fmt: on
    def __init__(
            self,
            name: Identifier,
            is_implementation_specific: bool,
            arguments: Sequence[Argument],
            returns: Optional[TypeAnnotation],
            description: Optional[Description],
            contracts: Contracts,
            body: Sequence[ast.AST],
            parsed: parse.Method,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.is_implementation_specific = is_implementation_specific
        self.arguments = arguments
        self.returns = returns
        self.description = description
        self.contracts = contracts
        self.body = body
        self.parsed = parsed

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class Constructor:
    """
    Represent an understood constructor of a class stacked.

    The constructor is expected to be stacked from the class and all the antecedents.
    """

    #: Arguments of the constructor method
    arguments: Final[Sequence[Argument]]

    #: Contracts of the constructor method
    contracts: Final[Contracts]

    #: If set, we need to provide a snippet for the constructor
    is_implementation_specific: bool

    #: Interpreted statements of the constructor, stacked over all the ancestors
    statements: Final[Sequence[construction.AssignArgument]]

    #: Map argument name 🠒 argument
    arguments_by_name: Final[Mapping[Identifier, Argument]]

    # fmt: on
    @require(
        lambda arguments: len(arguments) == len(set(arg.name for arg in arguments))
    )
    @ensure(
        lambda self:
        len(self.arguments) == len(self.arguments_by_name)
        and all(
            (
                    mapped_arg := self.arguments_by_name.get(argument.name, None),
                    mapped_arg is not None and id(mapped_arg) == id(argument)
            )[1]
            for argument in self.arguments
        ), "``arguments_by_name`` consistent"
    )
    # fmt: off
    def __init__(
            self,
            arguments: Sequence[Argument],
            contracts: Contracts,
            is_implementation_specific: bool,
            statements: Sequence[construction.AssignArgument],
    ) -> None:
        self.arguments = arguments
        self.contracts = contracts
        self.is_implementation_specific = is_implementation_specific

        # The calls to the super constructors must be in-lined before.
        self.statements = statements

        self.arguments_by_name = {
            argument.name: argument
            for argument in self.arguments
        }

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return f"<{_MODULE_NAME}.{self.__class__.__name__} at 0x{id(self):x}>"


class EnumerationLiteral:
    """Represent a single enumeration literal."""

    def __init__(
            self,
            name: Identifier,
            value: Identifier,
            description: Optional[Description],
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

    # TODO-BEFORE-RELEASE (mristin, 2021-12-13):
    #  document all properties, also do the same for Class, Method etc.

    #: Map literals by their identifiers
    literals_by_name: Final[Mapping[str, EnumerationLiteral]]

    #: Collect IDs (with :py:func:`id`) of the literal objects in a set
    literal_id_set: Final[FrozenSet[int]]

    def __init__(
            self,
            name: Identifier,
            literals: Sequence[EnumerationLiteral],
            is_superset_of: Sequence["Enumeration"],
            description: Optional[Description],
            parsed: parse.Enumeration,
    ) -> None:
        self.name = name
        self.literals = literals
        self.is_superset_of = is_superset_of
        self.description = description
        self.parsed = parsed

        self.literals_by_name: Mapping[str, EnumerationLiteral] = {
            literal.name: literal for literal in self.literals
        }

        self.literal_id_set = frozenset(id(literal) for literal in literals)


class Class:
    """Represent a class implementing zero, one or more interfaces."""

    #: Map all properties by their identifiers to the corresponding objects
    properties_by_name: Final[Mapping[Identifier, Property]]

    #: Collect IDs (with :py:func:`id`) of the property objects in a set
    property_id_set: Final[FrozenSet[int]]

    #: Collect IDs (with :py:func:`id`) of the invariant objects in a set
    invariant_id_set: Final[FrozenSet[int]]

    #: Collect IDs (with :py:func:`id`) of the interface objects in a set
    interface_id_set: Final[FrozenSet[int]]

    # fmt: off
    @require(
        lambda interfaces:
        len(interfaces) == len(set(identifier for identifier in interfaces)),
        "No duplicate interfaces"
    )
    @require(
        lambda properties:
        len(properties) == len(set(prop.name for prop in properties)),
        "No duplicate properties"
    )
    @require(
        lambda methods:
        len(methods) == len(set(method.name for method in methods)),
        "No duplicate methods"
    )
    # fmt: on
    def __init__(
            self,
            name: Identifier,
            interfaces: Sequence["Interface"],
            is_implementation_specific: bool,
            properties: Sequence[Property],
            methods: Sequence[Method],
            constructor: Constructor,
            invariants: Sequence[Invariant],
            serialization: Serialization,
            description: Optional[Description],
            parsed: parse.Class,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.interfaces = interfaces
        self.is_implementation_specific = is_implementation_specific
        self.properties = properties
        self.methods = methods
        self.constructor = constructor
        self.invariants = invariants
        self.serialization = serialization
        self.description = description
        self.parsed = parsed

        self.properties_by_name: Mapping[Identifier, Property] = {
            prop.name: prop for prop in self.properties
        }

        self.property_id_set = frozenset(id(prop) for prop in self.properties)
        self.invariant_id_set = frozenset(id(inv) for inv in self.invariants)
        self.interface_id_set = frozenset(
            id(interface) for interface in self.interfaces
        )

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


Symbol = Union[Interface, Enumeration, Class]

T = TypeVar("T")  # pylint: disable=invalid-name


class MetaModel:
    """Collect information about the underlying meta-model."""

    #: Description of the meta-model extracted from the docstring
    description: Final[Optional[Description]]

    #: Specify the URL of the book that the meta-model is based on
    book_url: Final[str]

    #: Specify the version of the book that the meta-model is based on
    book_version: Final[str]

    def __init__(
            self, book_url: str, book_version: str, description: Optional[Description]
    ) -> None:
        self.book_url = book_url
        self.book_version = book_version
        self.description = description


class SymbolTable:
    """Represent all the symbols of the intermediate representation."""

    #: List of all symbols that we need for the code generation
    symbols: Final[Sequence[Symbol]]

    #: List of all functions used in the verification
    verification_functions: Final[Sequence[Method]]

    #: Map verification functions by their name
    verification_functions_by_name: Final[Mapping[Identifier, Method]]

    #: Type to be used to represent a ``Ref[T]``
    ref_association: Final[Symbol]

    #: Additional information about the source meta-model
    meta_model: Final[MetaModel]

    _name_to_symbol: Final[Mapping[Identifier, Symbol]]

    # fmt: off
    @require(
        lambda symbols: (
                names := [symbol.name for symbol in symbols],
                len(names) == len(set(names)),
        )[1],
        "Symbol names unique",
    )
    @require(
        lambda verification_functions:
        all(
            func.is_implementation_specific
            for func in verification_functions
        ),
        "All verification functions are implementation-specific"
    )
    @ensure(
        lambda self:
        all(
            id(self.verification_functions_by_name[func.name]) == id(func)
            for func in self.verification_functions
        )
        and len(self.verification_functions_by_name) == len(
            self.verification_functions),
        "The verification functions and their mapping by name are consistent"
    )
    # fmt: on
    def __init__(
            self,
            symbols: Sequence[Symbol],
            verification_functions: Sequence[Method],
            ref_association: Symbol,
            meta_model: parse.MetaModel,
    ) -> None:
        """Initialize with the given values and map symbols to name."""
        self.symbols = symbols
        self.verification_functions = verification_functions
        self.ref_association = ref_association
        self.meta_model = meta_model

        self.verification_functions_by_name = {
            func.name: func
            for func in self.verification_functions
        }

        self._name_to_symbol = {symbol.name: symbol for symbol in symbols}

    def find(self, name: Identifier) -> Optional[Symbol]:
        """Find the symbol with the given ``name``."""
        return self._name_to_symbol.get(name, None)

    def must_find(self, name: Identifier) -> Symbol:
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


InterfaceImplementers = MutableMapping[Interface, List[Class]]


def map_interface_implementers(symbol_table: SymbolTable) -> InterfaceImplementers:
    """
    Produce an inverted index from interfaces to implementing classes.

    The tracing is transitive over interfaces. For example, assume interfaces ``A``
    and ``B``, ``B extends A`` and a class ``C``, ``C implements B``. Then the class
    ``C`` will both appear as an implementer of ``B`` as well as of ``A``.
    """
    mapping = dict()  # type: MutableMapping[Interface, List[Class]]
    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        assert isinstance(symbol, Class)

        stack = []  # type: List[Interface]
        for interface in symbol.interfaces:
            stack.append(interface)

        while len(stack) > 0:
            interface = stack.pop()

            lst = mapping.get(interface, None)
            if lst is None:
                lst = []
                mapping[interface] = lst

            lst.append(symbol)

            for parent_id in interface.inheritances:
                stack.append(parent_id)

    return mapping


class SymbolReferenceInDoc(docutils.nodes.Inline, docutils.nodes.TextElement):
    """Represent a reference in the documentation to a symbol in the symbol table."""

    def __init__(
            self, symbol: Symbol, rawsource="", text="", *children, **attributes
    ) -> None:
        """Initialize with the given symbol and propagate the rest to the parent."""
        self.symbol = symbol
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes
        )


class PropertyReferenceInDoc:
    """Model a reference to a property, usually used in the docstrings."""

    @require(lambda symbol, prop: id(prop) in symbol.property_id_set)
    def __init__(self, symbol: Union[Class, Interface], prop: Property) -> None:
        self.symbol = symbol
        self.prop = prop


class EnumerationLiteralReferenceInDoc:
    """Model a reference to an enumeration literal, usually used in the docstrings."""

    @require(lambda symbol, literal: id(literal) in symbol.literal_id_set)
    def __init__(self, symbol: Enumeration, literal: EnumerationLiteral) -> None:
        self.symbol = symbol
        self.literal = literal


class AttributeReferenceInDoc(docutils.nodes.Inline, docutils.nodes.TextElement):
    """
    Represent a reference in the documentation to an "attribute".

    The attribute, in this context, refers to the role ``:attr:``. The references
    implies either a reference to a property of a class or a literal of an enumeration.
    """

    def __init__(
            self,
            reference: Union[PropertyReferenceInDoc, EnumerationLiteralReferenceInDoc],
            rawsource="",
            text="",
            *children,
            **attributes,
    ) -> None:
        """Initialize with ``property_name`` and propagate the rest to the parent."""
        self.reference = reference
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes
        )


def map_descendability(
        type_annotation: TypeAnnotation,
        ref_association: Symbol
) -> MutableMapping[TypeAnnotation, bool]:
    """
    Map the type annotation recursively by the descendability.

    The descendability means that the type annotation references an interface
    or a class *or* that it is a subscripted type annotation which subscribes one or
    more classes of the meta-model.

    The mapping is a form of caching. Otherwise, the time complexity would be quadratic
    if we queried at each type annotation subscript.

    The ``ref_association`` indicates which symbol to use for representing references
    within an AAS.
    """
    mapping = dict()  # type: MutableMapping[TypeAnnotation, bool]

    def recurse(a_type_annotation: TypeAnnotation) -> bool:
        """Recursively iterate over subscripted type annotations."""
        if isinstance(a_type_annotation, BuiltinAtomicTypeAnnotation):
            mapping[a_type_annotation] = False
            return False

        elif isinstance(a_type_annotation, OurAtomicTypeAnnotation):
            result = None  # type: Optional[bool]
            if isinstance(a_type_annotation.symbol, Enumeration):
                result = False
            elif isinstance(a_type_annotation.symbol, (Interface, Class)):
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

        elif isinstance(a_type_annotation, RefTypeAnnotation):
            result = None  # type: Optional[bool]

            if isinstance(ref_association, Enumeration):
                result = False
            elif isinstance(ref_association, (Interface, Class)):
                result = True
            else:
                assert_never(ref_association)

            assert result is not None
            mapping[a_type_annotation] = result
            return result

        else:
            assert_never(a_type_annotation)

    _ = recurse(a_type_annotation=type_annotation)

    return mapping


class _ConstructorArgumentOfClass:
    """Represent a constructor argument with its corresponding class."""

    def __init__(self, arg: Argument, cls: Class) -> None:
        """Initialize with the given values."""
        self.arg = arg
        self.cls = cls


def make_union_of_constructor_arguments(
        interface: Interface, implementers: Sequence[Class]
) -> Tuple[Optional[OrderedDict[Identifier, TypeAnnotation]], Optional[Error]]:
    """
    Make a union of all the constructor arguments over all the implementer classes.

    This union is necessary, for example, when you need to de-serialize an object, but
    you are not yet sure which concrete type it has. Hence you need to be prepared to
    de-serialize a yet-unknown *subset* of the properties of *this* union when you start
    de-serializing an object of type ``interface``.
    """
    errors = []  # type: List[Error]

    arg_union = collections.OrderedDict(
    )  # type: OrderedDict[Identifier, List[_ConstructorArgumentOfClass]]

    # region Collect

    for implementer in implementers:
        for arg in implementer.constructor.arguments:
            lst = arg_union.get(arg.name, None)
            if lst is None:
                lst = []
                arg_union[arg.name] = lst

            lst.append(_ConstructorArgumentOfClass(arg=arg, cls=implementer))

            another_arg = arg_union.get(arg.name, None)

    # endregion

    # region Resolve

    resolution = collections.OrderedDict(
    )  # type: OrderedDict[Identifier, TypeAnnotation]

    for arg_name, args_of_clses in arg_union.items():
        # NOTE (mristin, 2021-12-19):
        # We have to check that the arguments share the same type. We have to allow
        # that the non-nullability constraint is strengthened since implementers can
        # strengthen the invariants.

        # This is the argument that defines the current resolved type.
        defining_arg = None  # type: Optional[_ConstructorArgumentOfClass]

        def normalize_type_annotation(type_anno: TypeAnnotation) -> TypeAnnotation:
            """Normalize the type annotation by removing prefix ``Optional``'s."""
            while isinstance(type_anno, OptionalTypeAnnotation):
                type_anno = type_anno.value

            return type_anno

        for arg_of_cls in args_of_clses:
            # Set if the resolution not possible for the current argument
            inconsistent = False

            if defining_arg is None:
                defining_arg = arg_of_cls
            else:
                if type_annotations_equal(
                        defining_arg.arg.type_annotation,
                        arg_of_cls.arg.type_annotation
                ):
                    # Leave the previous argument the defining one
                    continue
                else:
                    if type_annotations_equal(
                            normalize_type_annotation(defining_arg.arg.type_annotation),
                            normalize_type_annotation(arg_of_cls.arg.type_annotation)
                    ):
                        # NOTE (mristin, 2021-12-19):
                        # The type with ``Optional`` will win the resolution so that
                        # we allow for strengthening of invariants.

                        if isinstance(
                                defining_arg.arg.type_annotation,
                                OptionalTypeAnnotation
                        ):
                            # The defining argument wins.
                            continue
                        elif isinstance(
                                arg_of_cls.arg.type_annotation,
                                OptionalTypeAnnotation
                        ):
                            # The current argument wins.
                            defining_arg = arg_of_cls
                        else:
                            raise AssertionError(
                                f"Unexpected case: "
                                f"{arg_of_cls.arg.type_annotation=}, "
                                f"{defining_arg.arg.type_annotation=}")
                    else:
                        inconsistent = True

            if inconsistent:
                errors.append(
                    Error(
                        arg_of_cls.cls.parsed.node,
                        f"The constructor argument {defining_arg.arg.name!r} "
                        f"of the class {defining_arg.cls.name!r} "
                        f"has inconsistent type ({defining_arg.arg.type_annotation}) "
                        f"with the constructor argument {arg_of_cls.arg.name!r} "
                        f"of the class {arg_of_cls.cls.name!r} "
                        f"({arg_of_cls.arg.type_annotation}. "
                        f"This is a blocker for generating efficient code for "
                        f"JSON de-serialization of the interface {interface.name!r} "
                        f"(which both {defining_arg.cls.name!r} and "
                        f"{arg_of_cls.cls.name!r} implement).",
                    )
                )

            # endregion

        assert defining_arg is not None, "Expected to be set before"

        resolution[defining_arg.arg.name] = defining_arg.arg.type_annotation

    if len(errors) > 0:
        return None, Error(
            interface.parsed.node,
            f"Failed to make a union of constructor arguments "
            f"over all implementer classes of interface {interface.name}",
            errors,
        )

    return resolution, None


def collect_ids_of_interfaces_in_properties(symbol_table: SymbolTable) -> Set[int]:
    """
    Collect the IDs of the interfaces occurring in type annotations of the properties.

    The IDs refer to IDs of the Python objects in this context.
    """
    result = set()  # type: Set[int]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, Enumeration):
            continue

        elif isinstance(symbol, (Interface, Class)):
            for prop in symbol.properties:
                type_anno = prop.type_annotation

                old_type_anno = None  # type: Optional[TypeAnnotation]
                while True:
                    if isinstance(type_anno, OptionalTypeAnnotation):
                        # noinspection PyUnresolvedReferences
                        type_anno = type_anno.value
                    elif isinstance(type_anno, ListTypeAnnotation):
                        type_anno = type_anno.items
                    elif isinstance(type_anno, RefTypeAnnotation):
                        type_anno = type_anno.value
                    elif isinstance(type_anno, BuiltinAtomicTypeAnnotation):
                        break
                    elif isinstance(type_anno, OurAtomicTypeAnnotation):
                        if isinstance(type_anno.symbol, Interface):
                            result.add(id(type_anno.symbol))

                        break
                    else:
                        assert_never(type_anno)

                    assert old_type_anno is not type_anno, "Loop invariant"
                    old_type_anno = type_anno
        else:
            assert_never(symbol)

    return result
