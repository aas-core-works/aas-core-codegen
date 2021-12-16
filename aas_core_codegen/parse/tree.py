"""Provide our own abstract syntax tree for contract transpilation."""
import abc
import ast
import enum
from typing import Sequence, Union, Generic, TypeVar

from icontract import DBC

from aas_core_codegen import stringify
from aas_core_codegen.common import Identifier

T = TypeVar("T")


class Node(abc.ABC):
    """Represent an abstract node of our syntax tree."""

    def __init__(self, original_node: ast.AST) -> None:
        """Initialize with the given values."""
        self.original_node = original_node

    def __str__(self) -> str:
        """Provide a human-readable representation of the instance."""
        return dump(self)

    @abc.abstractmethod
    def transform(self, transformer: "Transformer[T]") -> T:
        """Accept the transformer."""
        raise NotImplementedError()

    @abc.abstractmethod
    def visit(self, visitor: "Visitor") -> None:
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
            self, instance: "Expression", name: Identifier, original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.instance = instance
        self.name = name

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_member(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_member(self)


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
            left: "Expression",
            op: Comparator,
            right: "Expression",
            original_node: ast.AST,
    ) -> None:
        Node.__init__(self, original_node=original_node)
        self.left = left
        self.op = op
        self.right = right

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_comparison(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_comparison(self)


class Implication(Expression):
    """Represent an implication of the form ``A => B``."""

    def __init__(
            self, antecedent: "Expression", consequent: "Expression",
            original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.antecedent = antecedent
        self.consequent = consequent

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_implication(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_implication(self)


class MethodCall(Expression):
    """Represent a method call."""

    def __init__(
            self, member: Member, args: Sequence["Expression"], original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.member = member
        self.args = args

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_method_call(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_method_call(self)


class FunctionCall(Expression):
    """Represent a function call."""

    def __init__(
            self, name: Identifier, args: Sequence["Expression"], original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.name = name
        self.args = args

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_function_call(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_function_call(self)


class Constant(Expression):
    """Represent a constant value."""

    def __init__(
            self, value: Union[bool, int, float, str], original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.value = value

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_constant(self)
    
    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_constant(self)


class IsNone(Expression):
    """Represent a check whether something ``is None``."""

    def __init__(self, value: Expression, original_node: ast.AST) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.value = value

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_is_none(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_is_none(self)


class IsNotNone(Expression):
    """Represent a check whether something ``is not None``."""

    def __init__(self, value: Expression, original_node: ast.AST) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.value = value

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_is_not_none(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_is_not_none(self)


class Name(Expression):
    """Represent an access to a variable with the given name."""

    def __init__(self, identifier: Identifier, original_node: ast.AST) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.identifier = identifier

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_name(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_name(self)


class And(Expression):
    """Represent a conjunction."""

    def __init__(self, values: Sequence[Expression], original_node: ast.AST) -> None:
        Node.__init__(self, original_node=original_node)
        self.values = values

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_and(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_and(self)
        
        
class Or(Expression):
    """Represent a disjunction."""

    def __init__(self, values: Sequence[Expression], original_node: ast.AST) -> None:
        Node.__init__(self, original_node=original_node)
        self.values = values

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_or(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_or(self)


class Declaration(Statement):
    """Declare a variable."""

    def __init__(
            self, identifier: Identifier, value: Expression, original_node: ast.AST
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.identifier = identifier
        self.value = value

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_declaration(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_declaration(self)
        

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
            original_node: ast.AST,
    ) -> None:
        """Initialize with the given values."""
        Node.__init__(self, original_node=original_node)
        self.declarations = declarations
        self.expression = expression

    def transform(self, transformer: "Transformer[T]") -> None:
        """Accept the transformer."""
        return transformer.transform_expression_with_declarations(self)

    def visit(self, visitor: "Visitor") -> None:
        """Accept the visitor."""
        visitor.visit_expression_with_declarations(self)


class Visitor(DBC):
    """
    Visit all the nodes in the AST.
    
    The default action for the generic visitor is to descend recursively into all the
    children nodes.
    """

    def visit(self, node: Node) -> None:
        """Dispatch to the appropriate visitation method."""
        node.visit(self)

    def visit_member(self, node: Member) -> None:
        """Visit a member to something."""
        self.visit(node.instance)

    def visit_comparison(self, node: Comparison) -> None:
        """Visit a comparison to something."""
        self.visit(node.left)
        self.visit(node.right)

    def visit_implication(self, node: Implication) -> None:
        """Visit an implication to something."""
        self.visit(node.antecedent)
        self.visit(node.consequent)

    def visit_method_call(self, node: MethodCall) -> None:
        """Visit a method call into something."""
        self.visit(node.member)
        for arg in node.args:
            self.visit(arg)

    def visit_function_call(self, node: FunctionCall) -> None:
        """Visit a function call into something."""
        for arg in node.args:
            self.visit(arg)

    def visit_constant(self, node: Constant) -> None:
        """Visit a constant into something."""
        pass

    def visit_is_none(self, node: IsNone) -> None:
        """Visit an is-none check into something."""
        self.visit(node.value)

    def visit_is_not_none(self, node: IsNotNone) -> None:
        """Visit an is-not-none check into something."""
        self.visit(node.value)

    def visit_name(self, node: Name) -> None:
        """Visit a variable access into something."""
        pass

    def visit_and(self, node: And) -> None:
        """Visit a conjunction into something."""
        for value in node.values:
            self.visit(value)

    def visit_or(self, node: Or) -> None:
        """Visit a disjunction into something."""
        for value in node.values:
            self.visit(value)

    def visit_declaration(self, node: Declaration) -> None:
        """Visit a variable declaration into something."""
        self.visit(node.value)

    def visit_expression_with_declarations(
            self, node: ExpressionWithDeclarations
    ) -> None:
        """Visit an expression with variable declarations into something."""
        for declaration in node.declarations:
            self.visit(declaration)

        self.visit(node.expression)


class Transformer(Generic[T], DBC):
    """Transform our AST into something."""

    def transform(self, node: Node) -> None:
        """Dispatch to the appropriate transformation method."""
        return node.transform(self)

    @abc.abstractmethod
    def transform_member(self, node: Member) -> None:
        """Transform a member to something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_comparison(self, node: Comparison) -> None:
        """Transform a comparison to something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_implication(self, node: Implication) -> None:
        """Transform an implication to something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_method_call(self, node: MethodCall) -> None:
        """Transform a method call into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_function_call(self, node: FunctionCall) -> None:
        """Transform a function call into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_constant(self, node: Constant) -> None:
        """Transform a constant into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_is_none(self, node: IsNone) -> None:
        """Transform an is-none check into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_is_not_none(self, node: IsNotNone) -> None:
        """Transform an is-not-none check into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_name(self, node: Name) -> None:
        """Transform a variable access into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_and(self, node: And) -> None:
        """Transform a conjunction into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_or(self, node: Or) -> None:
        """Transform a disjunction into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_declaration(self, node: Declaration) -> None:
        """Transform a variable declaration into something."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_expression_with_declarations(
            self, node: ExpressionWithDeclarations
    ) -> None:
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
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_comparison(self, node: Comparison) -> stringify.Entity:
        return stringify.Entity(
            name=Comparison.__name__,
            properties=[
                stringify.Property("left", self.transform(node.left)),
                stringify.Property("op", str(node.op.value)),
                stringify.Property("right", self.transform(node.right)),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_implication(self, node: Implication) -> stringify.Entity:
        return stringify.Entity(
            name=Implication.__name__,
            properties=[
                stringify.Property("antecedent", self.transform(node.antecedent)),
                stringify.Property("consequent", self.transform(node.consequent)),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_method_call(self, node: MethodCall) -> stringify.Entity:
        return stringify.Entity(
            name=MethodCall.__name__,
            properties=[
                stringify.Property("member", self.transform(node.member)),
                stringify.Property("args", [self.transform(arg) for arg in node.args]),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_function_call(self, node: FunctionCall) -> stringify.Entity:
        return stringify.Entity(
            name=FunctionCall.__name__,
            properties=[
                stringify.Property("name", node.name),
                stringify.Property("args", [self.transform(arg) for arg in node.args]),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_constant(self, node: Constant) -> stringify.Entity:
        return stringify.Entity(
            name=Constant.__name__,
            properties=[
                stringify.Property("value", node.value),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_is_none(self, node: IsNone) -> stringify.Entity:
        return stringify.Entity(
            name=IsNone.__name__,
            properties=[stringify.Property("value", self.transform(node.value))],
        )

    def transform_is_not_none(self, node: IsNotNone) -> stringify.Entity:
        return stringify.Entity(
            name=IsNotNone.__name__,
            properties=[
                stringify.Property("value", self.transform(node.value)),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_name(self, node: Name) -> stringify.Entity:
        return stringify.Entity(
            name=Name.__name__,
            properties=[
                stringify.Property("identifier", node.identifier),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_and(self, node: And) -> stringify.Entity:
        return stringify.Entity(
            name=And.__name__,
            properties=[
                stringify.Property(
                    "values", [self.transform(value) for value in node.values]
                ),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_or(self, node: Or) -> stringify.Entity:
        return stringify.Entity(
            name=Or.__name__,
            properties=[
                stringify.Property(
                    "values", [self.transform(value) for value in node.values]
                ),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_declaration(self, node: Declaration) -> stringify.Entity:
        return stringify.Entity(
            name=Declaration.__name__,
            properties=[
                stringify.Property("identifier", node.identifier),
                stringify.Property("value", self.transform(node.value)),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )

    def transform_expression_with_declarations(
            self, node: ExpressionWithDeclarations
    ) -> stringify.Entity:
        return stringify.Entity(
            name=Declaration.__name__,
            properties=[
                stringify.Property(
                    "declarations",
                    [self.transform(declaration) for declaration in node.declarations],
                ),
                stringify.Property("expression", self.transform(node.expression)),
                stringify.PropertyEllipsis("original_node", node.original_node),
            ],
        )


def dump(node: Node) -> str:
    """Produce a string representation of the tree."""
    transformer = _StringifyTransformer()
    return stringify.dump(transformer.transform(node=node))
