"""Provide types of the intermediate representation."""
import ast
import enum
import pathlib
from typing import (
    Sequence, Optional, Union, TypeVar, Mapping, MutableMapping, List)

import docutils.nodes
from icontract import require, invariant

from aas_core_csharp_codegen import parse
from aas_core_csharp_codegen.common import Identifier, assert_never
from aas_core_csharp_codegen.intermediate import construction
from aas_core_csharp_codegen.parse import BUILTIN_ATOMIC_TYPES
from aas_core_csharp_codegen.specific_implementations import ImplementationKey

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
            parsed: parse.Property,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.type_annotation = type_annotation
        self.description = description
        self.is_readonly = is_readonly
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


class Interface:
    """
    Represent an interface with methods mapped to signatures.

    We also include the properties so that we can generate the getters and setters at
    a later stage.
    """

    def __init__(
            self,
            name: Identifier,
            inheritances: Sequence[Identifier],
            signatures: Sequence[Signature],
            properties: Sequence[Property],
            description: Optional[Description],
            parsed: parse.Entity,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.inheritances = inheritances
        self.signatures = signatures
        self.properties = properties
        self.description = description
        self.parsed = parsed


class Invariant:
    """Represent an invariant of a class."""

    def __init__(
            self,
            description: Optional[str],
            parsed: parse.Invariant
    ) -> None:
        self.description = description
        # TODO: add body once we can translate it
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
    """
    Represent a method of a class.

    If :py:attr:`implementation_key` is specified, the method is considered
    implementation-specific.
    """

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
            implementation_key: Optional[ImplementationKey],
            arguments: Sequence[Argument],
            returns: Optional[TypeAnnotation],
            description: Optional[Description],
            contracts: Contracts,
            body: Sequence[ast.AST],
            parsed: parse.Method,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.implementation_key = implementation_key
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

    The constructor is expected to be stacked from the entity and all the antecedents.

    If :py:attr:`implementation_key` is specified, the constructor is considered
    implementation-specific.
    """

    @require(
        lambda arguments: len(arguments) == len(set(arg.name for arg in arguments))
    )
    def __init__(
            self,
            arguments: Sequence[Argument],
            contracts: Contracts,
            implementation_key: Optional[ImplementationKey],
            statements: Sequence[construction.AssignArgument],
    ) -> None:
        self.arguments = arguments
        self.contracts = contracts
        self.implementation_key = implementation_key

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
            description: Optional[Description],
            parsed: parse.Enumeration,
    ) -> None:
        self.name = name
        self.literals = literals
        self.description = description
        self.parsed = parsed

        self.literals_by_name: Mapping[str, EnumerationLiteral] = {
            literal.name: literal
            for literal in self.literals
        }


class Class:
    """
    Represent a class implementing zero, one or more interfaces.

    If :py:attr:`implementation_key` is specified, the constructor is considered
    implementation-specific.
    """

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
            interfaces: Sequence[Identifier],
            implementation_key: Optional[ImplementationKey],
            properties: Sequence[Property],
            methods: Sequence[Method],
            constructor: Constructor,
            invariants: Sequence[Invariant],
            description: Optional[Description],
            parsed: parse.Entity,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.interfaces = interfaces
        self.implementation_key = implementation_key
        self.properties = properties
        self.methods = methods
        self.constructor = constructor
        self.invariants = invariants
        self.description = description
        self.parsed = parsed

        self.properties_by_name: Mapping[str, Property] = {
            prop.name: prop for prop in self.properties
        }

        self.property_id_set = frozenset(id(prop) for prop in self.properties)
        self.invariant_id_set = frozenset(id(inv) for inv in self.invariants)


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

        stack = []  # type: List[Identifier]
        for interface_id in symbol.interfaces:
            stack.append(interface_id)

        while len(stack) > 0:
            interface_id = stack.pop()
            interface = symbol_table.must_find(name=interface_id)
            assert isinstance(interface, Interface), (
                f"Expected an interface given its identifier: {interface_id}")

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
    """Represent a reference in the documentation to a property of an entity."""

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

    The descendability means that the type annotation references an entity (an interface
    or a class) *or* that it is a subscripted type annotation which subscribes one or
    more entities of the meta-model.

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
