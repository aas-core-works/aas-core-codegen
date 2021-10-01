"""Provide the types into which we parse the original meta-model."""
import ast
import pathlib
from typing import Sequence, Optional, Union, Final, Mapping, Any

import docutils.nodes
from icontract import require, DBC, ensure

from aas_core_csharp_codegen.common import Identifier, assert_never

_MODULE_NAME = pathlib.Path(__file__).parent.name

BUILTIN_ATOMIC_TYPES = {"bool", "int", "float", "str"}

BUILTIN_COMPOSITE_TYPES = {
    "List",
    "Sequence",
    "Set",
    "Mapping",
    "MutableMapping",
    "Optional"
}


class AtomicTypeAnnotation:
    """Represent an atomic type annotation, such as ``Asset`` or ``int``."""

    def __init__(self, identifier: Identifier, node: ast.AST) -> None:
        """Initialize with the given values."""
        self.identifier = identifier
        self.node = node

    def __str__(self) -> str:
        return self.identifier

    def __repr__(self) -> str:
        """Represent the instance as a string for debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} "
            f"{self.identifier} at 0x{id(self):x}>"
        )


class SelfTypeAnnotation:
    """Provide a placeholder for the special argument ``self`` in a method"""

    def __str__(self) -> str:
        return "SELF"


class SubscriptedTypeAnnotation:
    """Represent a subscripted type annotation such as ``Optional[...]``."""

    def __init__(
            self, identifier: Identifier, subscripts: Sequence["TypeAnnotation"],
            node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        self.identifier = identifier
        self.subscripts = subscripts
        self.node = node

    def __str__(self) -> str:
        """Represent by reconstructing the type annotation heuristically."""
        return "".join(
            [self.identifier, "["]
            + [", ".join([str(subscript) for subscript in self.subscripts])]
            + ["]"]
        )

    def __repr__(self) -> str:
        """Represent the instance as a string for debugging."""
        subscripts_str = ", ".join(repr(subscript) for subscript in self.subscripts)
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} "
            f"{self.identifier} at 0x{id(self):x} "
            f"subscripts={subscripts_str}>"
        )


TypeAnnotation = Union[
    AtomicTypeAnnotation, SubscriptedTypeAnnotation, SelfTypeAnnotation
]


def final_in_type_annotation(type_annotation: TypeAnnotation) -> bool:
    """Check whether the type annotation contains ``Final`` type qualifier."""
    if isinstance(type_annotation, AtomicTypeAnnotation):
        if type_annotation.identifier == "Final":
            return True

        return False

    elif isinstance(type_annotation, SubscriptedTypeAnnotation):
        if type_annotation.identifier == "Final":
            return True

        for subscript in type_annotation.subscripts:
            if final_in_type_annotation(subscript):
                return True

        return False

    elif isinstance(type_annotation, SelfTypeAnnotation):
        return False

    else:
        assert_never(type_annotation)
        raise AssertionError(type_annotation)


class Description:
    """Represent a docstring describing something in the meta-model."""

    @require(lambda node: isinstance(node.value, str))
    def __init__(self, document: docutils.nodes.document, node: ast.Constant) -> None:
        """Initialize with the given values."""
        self.document = document
        self.node = node


class Property:
    """Represent a property of an entity."""

    # fmt: off
    @require(
        lambda type_annotation:
        not final_in_type_annotation(type_annotation),
        "The type qualifier ``Final`` extracted before and molded into ``is_readonly``"
    )
    # fmt: on
    def __init__(
            self,
            name: Identifier,
            type_annotation: TypeAnnotation,
            description: Optional[Description],
            is_readonly: bool,
            node: ast.AnnAssign,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.type_annotation = type_annotation
        self.description = description
        self.is_readonly = is_readonly
        self.node = node


class Default:
    """Represent a default value for an argument."""

    def __init__(self, value: Union[bool, int, float, str, None]) -> None:
        """Initialize with the given values."""
        self.value = value


class Argument:
    """Represent an argument of an entity's method."""

    @require(
        lambda type_annotation: not final_in_type_annotation(type_annotation),
        "No type qualifier ``Final`` expected in the type annotation of an argument",
    )
    def __init__(
            self,
            name: Identifier,
            type_annotation: TypeAnnotation,
            default: Optional[Default],
            node: ast.arg,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.type_annotation = type_annotation
        self.default = default
        self.node = node


class Invariant:
    """Represent an invariant of an entity."""

    def __init__(
            self,
            description: Optional[Description],
            condition: ast.Lambda,
            node: ast.AST
    ) -> None:
        self.description = description
        self.condition = condition
        self.node = node


class Contract:
    """Represent a contract of a method."""

    def __init__(
            self,
            args: Sequence[Identifier],
            description: Optional[Description],
            condition: ast.Lambda,
            node: ast.AST
    ) -> None:
        self.args = args
        self.description = description
        self.condition = condition
        self.node = node


class Snapshot:
    """Represent a snapshot of an OLD value capture before the method execution."""

    def __init__(
            self,
            args: Sequence[Identifier],
            name: Identifier,
            capture: ast.Lambda,
            node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        self.args = args
        self.name = name
        self.capture = capture
        self.node = node


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


# fmt: off
@ensure(
    lambda expr, result:
    not result
    or (
            isinstance(expr, ast.Expr)
            and isinstance(expr.value, ast.Constant)
            and isinstance(expr.value.value, str)
    )
)
# fmt: on
def is_string_expr(expr: ast.AST) -> bool:
    """Check that the expression is a string literal."""
    return (
            isinstance(expr, ast.Expr)
            and isinstance(expr.value, ast.Constant)
            and isinstance(expr.value.value, str)
    )


class Method:
    """Represent a method of an entity."""

    # fmt: off
    @require(
        lambda body: not (len(body) > 0) or not is_string_expr(expr=body[0]),
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
            node: ast.AST,
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.is_implementation_specific = is_implementation_specific
        self.arguments = arguments
        self.returns = returns
        self.description = description
        self.contracts = contracts
        self.body = body
        self.node = node

        self.argument_map = {
            argument.name: argument for argument in self.arguments
        }  # type: Mapping[Identifier, Argument]

    def __repr__(self) -> str:
        """Represent the instance as a string for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class Entity:
    """Represent an entity of the meta-model."""

    # fmt: off
    @require(
        lambda properties:
        (
                prop_names := [prop.name for prop in properties],
                len(prop_names) == len(set(prop_names))
        )[1],
        "Unique property names"
    )
    @require(
        lambda methods:
        (
                method_names := [method.name for method in methods],
                len(method_names) == len(set(method_names))
        )[1],
        "Unique methods names"
    )
    # fmt: on
    def __init__(
            self,
            name: Identifier,
            is_implementation_specific: bool,
            inheritances: Sequence[Identifier],
            properties: Sequence[Property],
            methods: Sequence[Method],
            invariants: Sequence[Invariant],
            description: Optional[Description],
            node: ast.ClassDef,
    ) -> None:
        self.name = name
        self.is_implementation_specific = is_implementation_specific
        self.inheritances = inheritances
        self.properties = properties
        self.methods = methods
        self.invariants = invariants
        self.description = description
        self.node = node

        self.property_map = {
            prop.name: prop for prop in properties
        }  # type: Mapping[Identifier, Property]

        self.method_map = {
            method.name: method for method in methods
        }  # type: Mapping[Identifier, Method]


class AbstractEntity(Entity):
    """
    Represent an abstract entity of the meta-model.

    For example, ``Referable``.
    """

    def __repr__(self) -> str:
        """Represent the entity with a name for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} "
            f"{self.name} at 0x{id(self):x}>"
        )


class ConcreteEntity(Entity):
    """
    Represent a concrete entity of the meta-model.

    For example, ``Asset``.
    """

    def __repr__(self) -> str:
        """Represent the entity with a name for easier debugging."""
        return (
            f"<{_MODULE_NAME}.{self.__class__.__name__} {self.name} at 0x{id(self):x}>"
        )


class EnumerationLiteral:
    """Represent a single enumeration literal."""

    def __init__(
            self,
            name: Identifier,
            value: Identifier,
            description: Optional[Description],
            node: ast.Assign
    ) -> None:
        self.name = name
        self.value = value
        self.description = description
        self.node = node


class Enumeration:
    """Represent an enumeration."""

    def __init__(
            self,
            name: Identifier,
            literals: Sequence[EnumerationLiteral],
            description: Optional[Description],
            node: ast.ClassDef,
    ) -> None:
        self.name = name
        self.literals = literals
        self.description = description
        self.node = node


Symbol = Union[AbstractEntity, ConcreteEntity, Enumeration]


class UnverifiedSymbolTable(DBC):
    """
    Represent the original entities in the meta-model.

    This symbol table is unverified and may contain inconsistencies.
    """

    #: List of parsed symbols
    symbols: Final[Sequence[Symbol]]

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
        """Find the symbol with the given name."""
        return self._name_to_symbol.get(name, None)

    def must_find(self, name: Identifier) -> Symbol:
        """
        Find the symbol with the given name.

        :raise: :py:class:`NameError` if it does not exist.
        """
        symbol = self._name_to_symbol.get(name, None)
        if symbol is None:
            raise NameError(
                f"The symbol {name!r} could not be found in the symbol table."
            )

        return symbol

    def must_find_entity(self, name: Identifier) -> Entity:
        """
        Find the entity with the given name.

        :param name: identifier of the entity
        :return: the entity
        :raise: :py:class:`NameError` if the name is not in the symbol table.
        :raise: :py:class:`TypeError` if the symbol is not an entity.
        """
        symbol = self._name_to_symbol.get(name, None)
        if symbol is None:
            raise NameError(
                f"The symbol {name!r} could not be found in the symbol table."
            )

        if not isinstance(symbol, Entity):
            raise TypeError(
                f"The symbol {name!r} is expected to be an entity, "
                f"but it is not: {symbol}"
            )

        return symbol


class SymbolTable(UnverifiedSymbolTable):
    """
    Represent a symbol table that has been locally verified.

    Locality in this context means that there are no dangling or obviously invalid
    inheritances, but higher-order relationships such as inheritance cycles has not
    been verified yet.
    """

    def __new__(cls, *args: Any, **kwargs: Any) -> "SymbolTable":
        raise AssertionError("Only for type annotation")
