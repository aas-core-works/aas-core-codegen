"""
Provide common functions for different algorithms for inference of the constraints.

The constraints are inferred based on the invariants, so the properties in this context
refer to member access in form of ``self.some_property``.
"""
from typing import Optional

from aas_core_codegen.common import Identifier

from aas_core_codegen.parse import (
    tree as parse_tree
)


# TODO: test this module


def match_property(node: parse_tree.Node) -> Optional[Identifier]:
    """Match an access to a property.

    For example, ``self.something`` will be a ``Property("something")``.
    """
    if (
            isinstance(node, parse_tree.Member)
            and isinstance(node.instance, parse_tree.Name)
            and node.instance.identifier == 'self'
    ):
        return node.name

    return None


class SingleArgFunctionOnProperty:
    """Represent a match of a function with a single argument on a property."""

    def __init__(self, function: Identifier, prop_name: Identifier) -> None:
        """Initialize with the given values."""
        self.function = function
        self.prop_name = prop_name


def match_single_arg_function_on_property(
        node: parse_tree.Node
) -> Optional[SingleArgFunctionOnProperty]:
    """
    Match a call of a function with a single argument on the property.

    Mind that we only match arguments, but ignore keyword arguments. This is due to
    simplicity of the implementation and this behavior might change in the future.
    """
    if not isinstance(node, parse_tree.FunctionCall):
        return None

    if len(node.args) != 1:
        return None

    prop_name = match_property(node.args[0])
    if prop_name is None:
        return None

    return SingleArgFunctionOnProperty(function=node.name, prop_name=prop_name)


class ConditionalOnProp:
    """Represent an invariant conditioned on an optional property."""

    def __init__(
            self,
            prop_name: Identifier,
            consequent: parse_tree.Expression
    ) -> None:
        """Initialize with the given values."""
        self.prop_name = prop_name
        self.consequent = consequent


def match_conditional_on_prop(node: parse_tree.Node) -> Optional[ConditionalOnProp]:
    """
    Match an invariant conditioned on an optional property.

    For example, ``not (self.some_prop is not None) or ...`` or
    ``self.some_prop is None or ...``.
    """
    if isinstance(node, parse_tree.Implication):
        if not isinstance(node.antecedent, parse_tree.IsNotNone):
            return None

        prop_name = match_property(node.antecedent.value)
        if prop_name is None:
            return None

        return ConditionalOnProp(prop_name=prop_name, consequent=node.consequent)

    elif isinstance(node, parse_tree.Or):
        if len(node.values) != 2:
            return None

        if not isinstance(node.values[0], parse_tree.IsNone):
            return None

        # noinspection PyUnresolvedReferences
        prop_name = match_property(node.values[0].value)
        if prop_name is None:
            return None

        return ConditionalOnProp(prop_name=prop_name, consequent=node.values[1])

    else:
        return None
