"""Provide our own abstract syntax tree for contract transpilation."""
import enum
from typing import Sequence, Union, Optional

from aas_core_csharp_codegen import stringify
from aas_core_csharp_codegen.common import Identifier, assert_never


class Expression:
    """Represent an expression in our abstract syntax tree."""

    def __str__(self) -> str:
        """Provide a human-readable representation of the instance."""
        return dump(self)


class Property(Expression):
    """Represent a loading of a property value."""

    def __init__(self, source: 'Expression', name: Identifier) -> None:
        """Initialize with the given values."""
        self.source = source
        self.name = name


class Self(Expression):
    """Represent a ``self`` instance."""


class Comparator(enum.Enum):
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"
    EQ = "EQ"
    NE = "NE"


class Comparison(Expression):
    """Represent a comparison."""

    def __init__(self, left: 'Expression', op: Comparator, right: 'Expression') -> None:
        self.left = left
        self.op = op
        self.right = right


class Implication(Expression):
    """Represent an implication of the form ``A => B``."""

    def __init__(self, antecedent: 'Expression', consequent: 'Expression') -> None:
        """Initialize with the given values."""
        self.antecedent = antecedent
        self.consequent = consequent


class KeywordArgument:
    """Represent a keyword argument as it is passed to a method or a function call."""

    def __init__(self, arg: Identifier, value: 'Expression') -> None:
        """Initialize with the given values."""
        self.arg = arg
        self.value = value


class MethodCall(Expression):
    """Represent a method call."""

    def __init__(
            self,
            reference: 'Expression',
            args: Sequence['Expression'],
            kwargs: Sequence['KeywordArgument']
    ) -> None:
        """Initialize with the given values."""
        self.reference = reference
        self.args = args
        self.kwargs = kwargs


class FunctionCall(Expression):
    """Represent a function call."""

    def __init__(
            self,
            name: Identifier,
            args: Sequence['Expression'],
            kwargs: Sequence[KeywordArgument]
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.args = args
        self.kwargs = kwargs


class Constant(Expression):
    """Represent a constant value."""

    def __init__(self, value: Union[bool, int, float, str]) -> None:
        """Initialize with the given values."""
        self.value = value

    def __str__(self) -> str:
        """Provide a human-readable representation of the instance."""
        return dump(self)


class IsNone(Expression):
    """Represent a check whether something is None."""

    def __init__(self, value: Expression) -> None:
        """Initialize with the given values."""
        self.value = value

    def __str__(self) -> str:
        """Provide a human-readable representation of the instance."""
        return dump(self)


class Name(Expression):
    """Represent an access to a variable with the given name."""

    def __init__(self, identifier: Identifier) -> None:
        """Initialize with the given values."""
        self.identifier = identifier


# TODO: add statements once we get there.
Node = Union[Expression]

Dumpable = Union[Expression, KeywordArgument]


def dump(dumpable: Dumpable) -> str:
    """Produce a string representation of the tree."""
    stringified = None  # type: Optional[stringify.Entity]

    if isinstance(dumpable, Property):
        stringified = stringify.Entity(
            name=Property.__name__,
            properties=[
                stringify.Property("source", dump(dumpable.source)),
                stringify.Property("name", dumpable.name)
            ])

    elif isinstance(dumpable, Self):
        stringified = stringify.Entity(name=Self.__name__, properties=[])

    elif isinstance(dumpable, Comparison):
        stringified = stringify.Entity(
            name=Comparison.__name__,
            properties=[
                stringify.Property("left", dump(dumpable.left)),
                stringify.Property("op", str(dumpable.op.value)),
                stringify.Property("right", dump(dumpable.right)),
            ])

    elif isinstance(dumpable, Implication):
        stringified = stringify.Entity(
            name=Implication.__name__,
            properties=[
                stringify.Property("antecedent", dump(dumpable.antecedent)),
                stringify.Property("consequent", dump(dumpable.consequent)),
            ])

    elif isinstance(dumpable, KeywordArgument):
        stringified = stringify.Entity(
            name=KeywordArgument.__name__,
            properties=[
                stringify.Property("arg", dumpable.arg),
                stringify.Property("value", dump(dumpable.value))
            ])

    elif isinstance(dumpable, MethodCall):
        stringified = stringify.Entity(
            name=MethodCall.__name__,
            properties=[
                stringify.Property("reference", dump(dumpable.reference)),
                stringify.Property("args", [dump(arg) for arg in dumpable.args]),
                stringify.Property(
                    "kwargs", [dump(kwarg) for kwarg in dumpable.kwargs])
            ])

    elif isinstance(dumpable, FunctionCall):
        stringified = stringify.Entity(
            name=FunctionCall.__name__,
            properties=[
                stringify.Property("name", dumpable.name),
                stringify.Property("args", [dump(arg) for arg in dumpable.args]),
                stringify.Property(
                    "kwargs", [dump(kwarg) for kwarg in dumpable.kwargs])
            ])

    elif isinstance(dumpable, Constant):
        stringified = stringify.Entity(
            name=Constant.__name__,
            properties=[stringify.Property("value", dumpable.value)])

    elif isinstance(dumpable, IsNone):
        stringified = stringify.Entity(
            name=IsNone.__name__,
            properties=[stringify.Property("value", dump(dumpable.value))])

    else:
        assert_never(dumpable)

    assert stringified is not None
    assert isinstance(stringified, stringify.Entity)
    assert stringified.name == dumpable.__name__
    stringify.assert_compares_against_dict(entity=stringified, obj=dumpable)

    return stringify.dump(stringified)
