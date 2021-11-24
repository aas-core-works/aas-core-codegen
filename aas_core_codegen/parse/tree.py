"""Provide our own abstract syntax tree for contract transpilation."""
import abc
import ast
import enum
from typing import Sequence, Union, Generic, TypeVar

from icontract import DBC, ensure

from aas_core_codegen import stringify
from aas_core_codegen.common import Identifier

T = TypeVar('T')


class Node(abc.ABC):
    """Represent an abstract node of our syntax tree."""

    def __init__(self, original_node: ast.AST) -> None:
        """Initialize with the given values."""
        self.original_node = original_node

    def __str__(self) -> str:
        """Provide a human-readable representation of the instance."""
        return dump(self)

    @abc.abstractmethod
    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        raise NotImplementedError()


class Statement(Node, abc.ABC):
    """Represent a statement in a program."""


class Expression(Node, abc.ABC):
    """Represent an expression in our abstract syntax tree."""


class Member(Expression):
    """
    Represent a member of an instance.

    A member is either a property or a method.
    """

    def __init__(
            self,
            instance: 'Expression',
            name: Identifier,
            original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.instance = instance
        self.name = name

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_member(self)


class Comparator(enum.Enum):
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"
    EQ = "EQ"
    NE = "NE"


class Comparison(Expression):
    """Represent a comparison."""

    def __init__(
            self,
            left: 'Expression',
            op: Comparator,
            right: 'Expression',
            original_node: ast.AST
    ) -> None:
        Node.__init__(self, original_node=original_node)
        self.left = left
        self.op = op
        self.right = right

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_comparison(self)


class Implication(Expression):
    """Represent an implication of the form ``A => B``."""

    def __init__(
            self,
            antecedent: 'Expression',
            consequent: 'Expression',
            original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.antecedent = antecedent
        self.consequent = consequent

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_implication(self)


class MethodCall(Expression):
    """Represent a method call."""

    def __init__(
            self,
            member: Member,
            args: Sequence['Expression'],
            original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.member = member
        self.args = args

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_method_call(self)


class FunctionCall(Expression):
    """Represent a function call."""

    def __init__(
            self,
            name: Identifier,
            args: Sequence['Expression'],
            original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.name = name
        self.args = args

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_function_call(self)


class Constant(Expression):
    """Represent a constant value."""

    def __init__(
            self,
            value: Union[bool, int, float, str],
            original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.value = value

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_constant(self)


class IsNone(Expression):
    """Represent a check whether something ``is None``."""

    def __init__(self, value: Expression, original_node: ast.AST) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.value = value

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_is_none(self)


class IsNotNone(Expression):
    """Represent a check whether something ``is not None``."""

    def __init__(self, value: Expression, original_node: ast.AST) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.value = value

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_is_not_none(self)


class Name(Expression):
    """Represent an access to a variable with the given name."""

    def __init__(self, identifier: Identifier, original_node: ast.AST) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.identifier = identifier

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_name(self)


class And(Expression):
    """Represent a conjunction."""

    def __init__(self, values: Sequence[Expression], original_node: ast.AST) -> None:
        Node.__init__(self, original_node=original_node)
        self.values = values

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_and(self)


class Or(Expression):
    """Represent a disjunction."""

    def __init__(self, values: Sequence[Expression], original_node: ast.AST) -> None:
        Node.__init__(self, original_node=original_node)
        self.values = values

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_or(self)


class Declaration(Statement):
    """Declare a variable."""

    def __init__(
            self,
            identifier: Identifier,
            value: Expression,
            original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.identifier = identifier
        self.value = value

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_declaration(self)


class ExpressionWithDeclarations(Expression):
    """
    Represent a declaration of a local variable followed by the expression.

    This abstract the code patterns such as ``(x := ..., len(x) > 0)[1]``, similar to,
    *e.g.*, short ``If`` statements in Golang.
    """

    def __init__(
            self,
            declarations: Sequence[Declaration],
            expression: Expression,
            original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.declarations = declarations
        self.expression = expression

    def transform(self, transformer: 'Transformer[T]') -> T:
        """Accept the transformer."""
        return transformer.transform_expression_with_declarations(self)


class Transformer(Generic[T], DBC):
    """Transform our AST into something."""

    def transform(self, node: Node) -> T:
        """Dispatch to the appropriate transformation method."""
        return node.transform(self)

    @abc.abstractmethod
    def transform_member(self, node: Member) -> T:
        """Transform a member to something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_comparison(self, node: Comparison) -> T:
        """Transform a comparison to something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_implication(self, node: Implication) -> T:
        """Transform an implication to something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_method_call(self, node: MethodCall) -> T:
        """Transform a method call into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_function_call(self, node: FunctionCall) -> T:
        """Transform a function call into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_constant(self, node: Constant) -> T:
        """Transform a constant into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_is_none(self, node: IsNone) -> T:
        """Transform an is-none check into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_is_not_none(self, node: IsNotNone) -> T:
        """Transform an is-not-none check into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_name(self, node: Name) -> T:
        """Transform a variable access into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_and(self, node: And) -> T:
        """Transform a conjunction into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_or(self, node: Or) -> T:
        """Transform a disjunction into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_declaration(self, node: Declaration) -> T:
        """Transform a variable declaration into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_expression_with_declarations(
            self, node: ExpressionWithDeclarations
    ) -> T:
        """Transform an expression with variable declarations into something."""
        raise NotImplementedError()


class _StringifyTransformer(Transformer[stringify.Entity]):
    """Transform a node into a stringifiable representation."""

    def transform(self, node: Node) -> stringify.Entity:
        """Dispatch to the appropriate transformation method."""
        result = node.transform(self)
        stringify.assert_compares_against_dict(entity=result, obj=node)
        return node.transform(self)

    def transform_member(self, node: Member) -> stringify.Entity:
        return stringify.Entity(
            name=Member.__name__,
            properties=[
                stringify.Property("instance", self.transform(node.instance)),
                stringify.Property("name", node.name),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_comparison(self, node: Comparison) -> stringify.Entity:
        return stringify.Entity(
            name=Comparison.__name__,
            properties=[
                stringify.Property("left", self.transform(node.left)),
                stringify.Property("op", str(node.op.value)),
                stringify.Property("right", self.transform(node.right)),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_implication(self, node: Implication) -> stringify.Entity:
        return stringify.Entity(
            name=Implication.__name__,
            properties=[
                stringify.Property("antecedent", self.transform(node.antecedent)),
                stringify.Property("consequent", self.transform(node.consequent)),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_method_call(self, node: MethodCall) -> stringify.Entity:
        return stringify.Entity(
            name=MethodCall.__name__,
            properties=[
                stringify.Property("member", self.transform(node.member)),
                stringify.Property("args", [self.transform(arg) for arg in node.args]),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_function_call(self, node: FunctionCall) -> stringify.Entity:
        return stringify.Entity(
            name=FunctionCall.__name__,
            properties=[
                stringify.Property("name", node.name),
                stringify.Property("args", [self.transform(arg) for arg in node.args]),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_constant(self, node: Constant) -> stringify.Entity:
        return stringify.Entity(
            name=Constant.__name__,
            properties=[
                stringify.Property("value", node.value),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_is_none(self, node: IsNone) -> stringify.Entity:
        return stringify.Entity(
            name=IsNone.__name__,
            properties=[stringify.Property("value", self.transform(node.value))])

    def transform_is_not_none(self, node: IsNotNone) -> stringify.Entity:
        return stringify.Entity(
            name=IsNotNone.__name__,
            properties=[
                stringify.Property("value", self.transform(node.value)),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_name(self, node: Name) -> stringify.Entity:
        return stringify.Entity(
            name=Name.__name__,
            properties=[
                stringify.Property("identifier", node.identifier),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_and(self, node: And) -> stringify.Entity:
        return stringify.Entity(
            name=And.__name__,
            properties=[
                stringify.Property(
                    "values", [self.transform(value) for value in node.values]),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_or(self, node: Or) -> stringify.Entity:
        return stringify.Entity(
            name=Or.__name__,
            properties=[
                stringify.Property(
                    "values", [self.transform(value) for value in node.values]),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_declaration(self, node: Declaration) -> stringify.Entity:
        return stringify.Entity(
            name=Declaration.__name__,
            properties=[
                stringify.Property("identifier", node.identifier),
                stringify.Property("value", self.transform(node.value)),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])

    def transform_expression_with_declarations(
            self, node: ExpressionWithDeclarations
    ) -> stringify.Entity:
        return stringify.Entity(
            name=Declaration.__name__,
            properties=[
                stringify.Property(
                    "declarations", [
                        self.transform(declaration)
                        for declaration in node.declarations
                    ]),
                stringify.Property("expression", self.transform(node.expression)),
                stringify.PropertyEllipsis("original_node", node.original_node)
            ])


def dump(node: Node) -> str:
    """Produce a string representation of the tree."""
    transformer = _StringifyTransformer()
    return stringify.dump(transformer.transform(node=node))
