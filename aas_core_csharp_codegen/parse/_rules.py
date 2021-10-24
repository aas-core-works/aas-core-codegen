"""
Define the parse rules for transforming Python AST to our custom AST.

This module provides translation from a very general Python AST to our more specific,
domain-related syntax.

For comparison, :py:mod:`aas_core_csharp_codegen.intermediate` is responsible for
semantic analysis, simplifications and resolution to environments and actual symbols.
"""

import abc
import ast
import os
import pathlib
from typing import Tuple, Optional, List, Mapping, Type, Sequence

from icontract import ensure

from aas_core_csharp_codegen.common import Identifier, Error
from aas_core_csharp_codegen.parse import tree

_AST_COMPARATOR_TO_OURS = {
    ast.Lt: tree.Comparator.LT,
    ast.LtE: tree.Comparator.LE,
    ast.Gt: tree.Comparator.GT,
    ast.GtE: tree.Comparator.GE,
    ast.Eq: tree.Comparator.EQ,
    ast.NotEq: tree.Comparator.NE
}  # type: Mapping[Type[ast.cmpop], tree.Comparator]


class _Parse(abc.ABC):
    """Define a parse rule from a Python AST node to our custom AST."""

    @abc.abstractmethod
    def matches(self, node: ast.AST) -> bool:
        """Return True if the node can be matched by the rule."""
        raise NotImplementedError()

    @abc.abstractmethod
    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        """Transform the Python node to our custom node."""
        raise NotImplementedError()


class _ParseComparison(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return (
                isinstance(node, ast.Compare)
                and len(node.ops) == 1
                and type(node.ops[0]) in _AST_COMPARATOR_TO_OURS
                and len(node.comparators) == 1
        )

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        left, error = ast_node_to_our_node(node.left)
        if error is not None:
            return None, error

        assert isinstance(left, tree.Expression), f"{left=}"

        op = _AST_COMPARATOR_TO_OURS[type(node.ops[0])]

        right, error = ast_node_to_our_node(node.comparators[0])
        if error is not None:
            return None, error

        assert isinstance(right, tree.Expression), f"{right=}"

        return tree.Comparison(left=left, op=op, right=right), None


class _ParseCall(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Call)

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        args = []  # type: List[tree.Expression]
        for arg_node in node.args:
            arg, error = ast_node_to_our_node(arg_node)
            if error is not None:
                return None, error

            if not isinstance(arg, tree.Expression):
                return None, Error(
                    arg_node,
                    f"Expected the argument to a call to be an expression, "
                    f"but got: {arg}")

            args.append(arg)

        kwargs = []  # type: List[tree.KeywordArgument]
        for kw_node in node.keywords:
            kw_value, error = ast_node_to_our_node(kw_node.value)
            if error is not None:
                return None, error

            if not isinstance(kw_value, tree.Expression):
                return None, Error(
                    kw_node,
                    f"Expected the keyword argument to a call to be an expression, "
                    f"but got: {kw_value}")

            kwargs.append(tree.KeywordArgument(arg=kw_node.arg, value=kw_value))

        if isinstance(node.func, ast.Name):
            return tree.FunctionCall(
                name=Identifier(node.func.id), args=args, kwargs=kwargs), None
        else:
            member, error = ast_node_to_our_node(node.func)
            if error is not None:
                return None, error

            assert isinstance(member, tree.Member), (
                f"Expected a member for {ast.dump(node.func)=}, but got: {member=}")

            return tree.MethodCall(member=member, args=args, kwargs=kwargs), None


class _ParseConstant(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return (
                isinstance(node, ast.Constant)
                and isinstance(node.value, (bool, int, float, str))
        )

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        return tree.Constant(value=node.value), None


class _ParseImplication(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return (
                isinstance(node, ast.BoolOp)
                and isinstance(node.op, ast.Or)
                and len(node.values) == 2
                and isinstance(node.values[0], ast.UnaryOp)
                and isinstance(node.values[0].op, ast.Not)
        )

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        antecedent, error = ast_node_to_our_node(node.values[0].operand)
        if error is not None:
            return None, error

        assert isinstance(antecedent, tree.Expression), f"{antecedent=}"

        consequent, error = ast_node_to_our_node(node.values[1])
        if error is not None:
            return None, error

        assert isinstance(consequent, tree.Expression), f"{consequent=}"

        return tree.Implication(antecedent=antecedent, consequent=consequent), None


class _ParseMember(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Attribute)

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        instance, error = ast_node_to_our_node(node.value)
        if error is not None:
            return None, error

        assert isinstance(instance, tree.Expression), f"{instance=}"

        return tree.Member(instance=instance, name=Identifier(node.attr)), None



class _ParseName(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Name)

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        return tree.Name(identifier=Identifier(node.id)), None


class _ParseIsNoneOrIsNotNone(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return (
                isinstance(node, ast.Compare)
                and len(node.ops) == 1
                and isinstance(node.ops[0], (ast.Is, ast.IsNot))
                and len(node.comparators) == 1
                and isinstance(node.comparators[0], ast.Constant)
                and node.comparators[0].value is None
        )

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        value, error = ast_node_to_our_node(node.left)
        if error is not None:
            return None, error

        if isinstance(node.ops[0], ast.Is):
            return tree.IsNone(value=value), None
        elif isinstance(node.ops[0], ast.IsNot):
            return tree.IsNotNone(value=value), None
        else:
            raise AssertionError(f"Unexpected: {node.ops[0]=}")


class _ParseAndOrOr(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return (
                isinstance(node, ast.BoolOp)
                and isinstance(node.op, (ast.And, ast.Or))
        )

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        values = []  # type: List[tree.Expression]
        for value_node in node.values:
            value, error = ast_node_to_our_node(value_node)
            if error is not None:
                return None, error

            values.append(value)

        if isinstance(node.op, ast.And):
            return tree.And(values=values), None
        elif isinstance(node.op, ast.Or):
            return tree.Or(values=values), None
        else:
            raise AssertionError(f"Unexpected: {node.op=}")


class _ParseExpressionWithDeclaration(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Tuple)
                and len(node.value.elts) == 2
                and isinstance(node.value.elts[0], ast.NamedExpr)
                and isinstance(node.slice, ast.Index)
                and isinstance(node.slice.value, ast.Constant)
                and node.slice.value.value == 1
        )

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        declaration, error = ast_node_to_our_node(node.value.elts[0])
        if error is not None:
            return None, error

        assert isinstance(declaration, tree.Declaration), f"{declaration=}"

        expression, error = ast_node_to_our_node(node.value.elts[1])
        if error is not None:
            return None, error

        assert isinstance(expression, tree.Expression), f"{expression=}"

        return tree.ExpressionWithDeclarations(
            declarations=[declaration],
            expression=expression), None


class _ParseDeclaration(_Parse):
    def matches(self, node: ast.AST) -> bool:
        return (
                isinstance(node, ast.NamedExpr)
                and isinstance(node.target, ast.Name)
        )

    def transform(self, node: ast.AST) -> Tuple[Optional[tree.Node], Optional[Error]]:
        value, error = ast_node_to_our_node(node.value)
        if error is not None:
            return None, error

        return (
            tree.Declaration(identifier=Identifier(node.target.id), value=value), None)

# TODO: continue here, implement generators and other constructs


_CHAIN_OF_RULES = [
    _ParseComparison(),
    _ParseCall(),
    _ParseConstant(),
    _ParseImplication(),
    _ParseMember(),
    _ParseName(),
    _ParseIsNoneOrIsNotNone(),
    _ParseAndOrOr(),
    _ParseExpressionWithDeclaration(),
    _ParseDeclaration()
]  # type: Sequence[_Parse]

# TODO: implement _Simplify(node) -> node


def _assert_chains_follow_file_structure() -> None:
    """
    Make sure that the chains of command follow the structure of the module.

    This check is necessary so that the rules can be directly followed in the source
    code. Otherwise, it is very hard to follow the chain if it differs from the order
    in which the classes are defined.
    """
    this_file = pathlib.Path(os.path.realpath(__file__))
    root = ast.parse(source=this_file.read_text(), filename=str(this_file))
    assert isinstance(root, ast.Module)

    expected_parse_names = [
        stmt.name
        for stmt in root.body
        if (
                isinstance(stmt, ast.ClassDef)
                and stmt.name.startswith("_Parse")
                and stmt.name != "_Parse"
        )
    ]  # type: List[str]

    parse_names_in_chain = [parse.__class__.__name__ for parse in _CHAIN_OF_RULES]

    assert expected_parse_names == parse_names_in_chain, (
        f"{expected_parse_names=} != {parse_names_in_chain=}")


_assert_chains_follow_file_structure()


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def ast_node_to_our_node(
        node: ast.AST
) -> Tuple[Optional[tree.Node], Optional[Error]]:
    """
    Parse the Python AST node into our custom AST.

    For example, this function is used to parse contract conditions into
    our representation which is later easier for processing.
    """
    for parse_rule in _CHAIN_OF_RULES:
        # NOTE(mristin, 2021-10-08):
        # Please leave the variables as they are to facilitate the eventual debugging
        # even though a more succinct code structure lures you.

        matches = parse_rule.matches(node)
        if matches:
            result, error = parse_rule.transform(node)

            if error is not None:
                return None, error

            return result, None

    return None, Error(
        node,
        f"The code matched no pattern for transpilation "
        f"at the parse stage: {ast.dump(node)}")
