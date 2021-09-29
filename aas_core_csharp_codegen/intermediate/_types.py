"""Provide types of the intermediate representation."""
import ast
import enum
import pathlib
from typing import Sequence, Optional, Union, TypeVar, Mapping

import docutils.nodes
from icontract import require

import aas_core_csharp_codegen.understand.constructor as understand_constructor
from aas_core_csharp_codegen import parse
from aas_core_csharp_codegen.common import Identifier
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


class SelfTypeAnnotation:
    """Provide a placeholder for the special argument ``self`` in a method"""

    def __str__(self) -> str:
        return "SELF"


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
    AtomicTypeAnnotation, SubscriptedTypeAnnotation, SelfTypeAnnotation
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


class Default:
    """Represent a default value for an argument."""

    def __init__(
            self, value: Union[bool, int, float, str, None], parsed: parse.Default
    ) -> None:
        """Initialize with the given values."""
        self.value = value
        self.parsed = parsed


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
            is_implementation_specific: bool,
            description: Optional[Description],
            parsed: parse.Entity,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.inheritances = inheritances
        self.signatures = signatures
        self.properties = properties
        self.is_implementation_specific = is_implementation_specific
        self.description = description
        self.parsed = parsed


class Contract:
    """Represent a contract of a method."""

    def __init__(
            self,
            args: Sequence[Identifier],
            description: Optional[Description],
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
                    for arg in postcondition.args if arg not in ('OLD', 'result')
                )
                and all(
                    arg in arg_set
                    for snapshot in contracts.snapshots
                    for arg in snapshot.args
                )
        )[1],
        "All arguments of contracts defined in method arguments"
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

    The constructor is expected to be stacked from the entity and all the antecedents.
    """

    @require(
        lambda arguments: len(arguments) == len(set(arg.name for arg in arguments))
    )
    def __init__(
            self,
            arguments: Sequence[Argument],
            contracts: Contracts,
            is_implementation_specific: bool,
            statements: Sequence[understand_constructor.AssignArgument],
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
            interfaces: Sequence[Identifier],
            is_implementation_specific: bool,
            properties: Sequence[Property],
            methods: Sequence[Method],
            constructor: Constructor,
            description: Optional[Description],
            parsed: parse.Entity,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.interfaces = interfaces
        self.is_implementation_specific = is_implementation_specific
        self.properties = properties
        self.methods = methods
        self.constructor = constructor
        self.description = description
        self.parsed = parsed


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
