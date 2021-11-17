"""Provide types of the intermediate representation."""
import ast
import enum
import pathlib
from typing import (
    Sequence, Optional, Union, TypeVar, Mapping, MutableMapping, List, Tuple)

import docutils.nodes
from icontract import require, invariant

from aas_core_csharp_codegen import parse
from aas_core_csharp_codegen.common import Identifier, assert_never, Error
from aas_core_csharp_codegen.intermediate import construction
from aas_core_csharp_codegen.parse import BUILTIN_ATOMIC_TYPES

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


assert (
        sorted(literal.value for literal in BuiltinAtomicType) ==
        sorted(BUILTIN_ATOMIC_TYPES)
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

    def __init__(self, symbol: 'Symbol', parsed: parse.TypeAnnotation) -> None:
        """Initialize with the given values."""
        self.symbol = symbol
        self.parsed = parsed

    def __str__(self) -> str:
        return self.symbol.name


class SubscriptedTypeAnnotation:
    """Represent a subscripted type annotation such as ``Mapping[..., ...]``."""


class ListTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``List[...]``."""

    def __init__(self, items: 'TypeAnnotation', parsed: parse.TypeAnnotation):
        self.items = items
        self.parsed = parsed

    def __str__(self) -> str:
        return f"List[{self.items}]"


class SequenceTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``Sequence[...]``."""

    def __init__(self, items: 'TypeAnnotation', parsed: parse.TypeAnnotation):
        self.items = items
        self.parsed = parsed

    def __str__(self) -> str:
        return f"Sequence[{self.items}]"


class SetTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``Set[...]``."""

    def __init__(self, items: 'TypeAnnotation', parsed: parse.TypeAnnotation):
        self.items = items
        self.parsed = parsed

    def __str__(self) -> str:
        return f"Set[{self.items}]"


class MappingTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``Mapping[..., ...]``."""

    def __init__(
            self, keys: 'TypeAnnotation', values: 'TypeAnnotation',
            parsed: parse.TypeAnnotation):
        self.keys = keys
        self.values = values
        self.parsed = parsed

    def __str__(self) -> str:
        return f"Mapping[{self.keys}, {self.values}]"


class MutableMappingTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``MutableMapping[..., ...]``."""

    def __init__(
            self, keys: 'TypeAnnotation', values: 'TypeAnnotation',
            parsed: parse.TypeAnnotation):
        self.keys = keys
        self.values = values
        self.parsed = parsed

    def __str__(self) -> str:
        return f"MutableMapping[{self.keys}, {self.values}]"


class OptionalTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``MutableMapping[..., ...]``."""

    def __init__(self, value: 'TypeAnnotation', parsed: parse.TypeAnnotation):
        self.value = value
        self.parsed = parsed

    def __str__(self) -> str:
        return f"Optional[{self.value}]"


TypeAnnotation = Union[
    AtomicTypeAnnotation, SubscriptedTypeAnnotation
]


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
    elif isinstance(that, SequenceTypeAnnotation):
        assert isinstance(other, SequenceTypeAnnotation)
        return type_annotations_equal(that.items, other.items)
    elif isinstance(that, SetTypeAnnotation):
        assert isinstance(other, SetTypeAnnotation)
        return type_annotations_equal(that.items, other.items)
    elif isinstance(that, MappingTypeAnnotation):
        assert isinstance(other, MappingTypeAnnotation)
        return (
                type_annotations_equal(that.keys, other.keys)
                and type_annotations_equal(that.values, other.values))
    elif isinstance(that, MutableMappingTypeAnnotation):
        assert isinstance(other, MutableMappingTypeAnnotation)
        return (
                type_annotations_equal(that.keys, other.keys)
                and type_annotations_equal(that.values, other.values))
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
            is_readonly: bool,
            implemented_for: Optional['Symbol'],
            parsed: parse.Property,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.type_annotation = type_annotation
        self.description = description
        self.is_readonly = is_readonly
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
            enumeration: 'Enumeration',
            literal: 'EnumerationLiteral',
            parsed: parse.Default
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


class JsonSerialization:
    """Specify the settings for JSON serialization of an interface or a class."""

    def __init__(self, with_model_type: bool) -> None:
        """Initialize with the given values."""
        self.with_model_type = with_model_type


class XmlSerialization:
    """Specify the settings for XML serialization of an interface or a class."""

    def __init__(self, property_as_text: Optional[Identifier]) -> None:
        """Initialize with the given values."""
        self.property_as_text = property_as_text


class Interface:
    """
    Represent an interface with methods mapped to signatures.

    We also include the properties so that we can generate the getters and setters at
    a later stage.
    """

    def __init__(
            self,
            name: Identifier,
            inheritances: Sequence['Interface'],
            signatures: Sequence[Signature],
            properties: Sequence[Property],
            json_serialization: JsonSerialization,
            description: Optional[Description],
            parsed: parse.Class,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.inheritances = inheritances
        self.signatures = signatures
        self.properties = properties
        self.json_serialization = json_serialization
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
            parsed: parse.Invariant
    ) -> None:
        self.description = description
        self.parsed = parsed


class Contract:
    """Represent a contract of a method."""

    def __init__(
            self,
            args: Sequence[Identifier],
            description: Optional[str],
            body: ast.AST,
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
            body: ast.AST,
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

    @require(
        lambda arguments: len(arguments) == len(set(arg.name for arg in arguments))
    )
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

    def __init__(
            self,
            name: Identifier,
            literals: Sequence[EnumerationLiteral],
            is_superset_of: Sequence['Enumeration'],
            description: Optional[Description],
            parsed: parse.Enumeration,
    ) -> None:
        self.name = name
        self.literals = literals
        self.is_superset_of = is_superset_of
        self.description = description
        self.parsed = parsed

        self.literals_by_name: Mapping[str, EnumerationLiteral] = {
            literal.name: literal
            for literal in self.literals
        }


class Class:
    """Represent a class implementing zero, one or more interfaces."""

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
            interfaces: Sequence['Interface'],
            is_implementation_specific: bool,
            properties: Sequence[Property],
            methods: Sequence[Method],
            constructor: Constructor,
            invariants: Sequence[Invariant],
            json_serialization: JsonSerialization,
            xml_serialization: XmlSerialization,
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
        self.json_serialization = json_serialization
        self.xml_serialization = xml_serialization
        self.description = description
        self.parsed = parsed

        self.properties_by_name: Mapping[Identifier, Property] = {
            prop.name: prop for prop in self.properties
        }

        self.property_id_set = frozenset(id(prop) for prop in self.properties)
        self.invariant_id_set = frozenset(id(inv) for inv in self.invariants)

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )

Symbol = Union[Interface, Enumeration, Class]

T = TypeVar("T")  # pylint: disable=invalid-name


class SymbolTable:
    """Represent all the symbols of the intermediate representation."""

    @require(
        lambda symbols: (
                names := [symbol.name for symbol in symbols],
                len(names) == len(set(names)),
        )[1],
        "Symbol names unique",
    )
    def __init__(self, symbols: Sequence[Symbol]) -> None:
        """Initialize with the given values and map symbols to name."""
        self.symbols = symbols
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


def map_interface_implementers(
        symbol_table: SymbolTable
) -> InterfaceImplementers:
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
            self, symbol: Symbol, rawsource='', text='', *children, **attributes
    ) -> None:
        """Initialize with the given symbol and propagate the rest to the parent."""
        self.symbol = symbol
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes)


class PropertyReferenceInDoc(docutils.nodes.Inline, docutils.nodes.TextElement):
    """Represent a reference in the documentation to a property of a class."""

    def __init__(
            self, property_name: str, rawsource='', text='', *children, **attributes
    ) -> None:
        """Initialize with ``property_name`` and propagate the rest to the parent."""
        self.property_name = property_name
        docutils.nodes.TextElement.__init__(
            self, rawsource, text, *children, **attributes)


def map_descendability(
        type_annotation: TypeAnnotation
) -> MutableMapping[TypeAnnotation, bool]:
    """
    Map the type annotation recursively by the descendability.

    The descendability means that the type annotation references an interface
    or a class *or* that it is a subscripted type annotation which subscribes one or
    more classes of the meta-model.

    The mapping is a form of caching. Otherwise, the time complexity would be quadratic
    if we queried at each type annotation subscript.
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

        elif isinstance(a_type_annotation, (
                ListTypeAnnotation,
                SequenceTypeAnnotation,
                SetTypeAnnotation)):
            result = recurse(a_type_annotation=a_type_annotation.items)
            mapping[a_type_annotation] = result
            return result

        elif isinstance(a_type_annotation, (
                MappingTypeAnnotation,
                MutableMappingTypeAnnotation
        )):
            result = recurse(a_type_annotation=a_type_annotation.values)
            mapping[a_type_annotation] = result
            return result

        elif isinstance(a_type_annotation, OptionalTypeAnnotation):
            result = recurse(a_type_annotation=a_type_annotation.value)
            mapping[a_type_annotation] = result
            return result

        else:
            assert_never(a_type_annotation)

    _ = recurse(a_type_annotation=type_annotation)

    return mapping


class _PropertyOfClass:
    """Represent the property with its corresponding class."""

    def __init__(self, prop: Property, cls: Class):
        """Initialize with the given values."""
        self.prop = prop
        self.cls = cls


def make_union_of_properties(
        interface: Interface,
        implementers: Sequence[Class]
) -> Tuple[Optional[MutableMapping[Identifier, TypeAnnotation]], Optional[Error]]:
    """Make a union of all the properties over all the implementer classes.

    This union is necessary, for example, when you need to de-serialize an object, but
    you are not yet sure which concrete type it has. Hence you need to be prepared to
    de-serialize a yet-unknown *subset* of the properties of *this* union when you start
    de-serializing an object of type ``interface``.
    """
    errors = []  # type: List[Error]

    property_union = dict()  # type: MutableMapping[Identifier, _PropertyOfClass]
    for implementer in implementers:
        for prop in implementer.properties:
            another_prop = property_union.get(prop.name, None)

            if another_prop is None:
                property_union[prop.name] = _PropertyOfClass(
                    cls=implementer, prop=prop)
            elif not type_annotations_equal(
                    prop.type_annotation,
                    another_prop.prop.type_annotation):
                errors.append(Error(
                    implementer.parsed.node,
                    f"The property {prop.name} of the class {implementer.name} "
                    f"has inconsistent type ({prop.type_annotation}) "
                    f"with the property {another_prop.prop.name} "
                    f"of the class {another_prop.cls.name} "
                    f"({another_prop.prop.type_annotation}. "
                    f"This is a blocker for generating efficient code for "
                    f"JSON de-serialization of the interface {interface.name} "
                    f"(which both {implementer.name} and "
                    f"{another_prop.cls.name} implement)."))
            else:
                # Everything is OK, the properties share the same type.
                pass

    if len(errors) > 0:
        return None, Error(
            interface.parsed.node,
            f"Failed to make a union of properties over all implementer classes of "
            f"interface {interface.name}",
            errors)

    return {
               prop_of_cls.prop.name: prop_of_cls.prop.type_annotation
               for prop_of_cls in property_union.values()
           }, None
