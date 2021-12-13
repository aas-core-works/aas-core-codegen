"""Infer the constraints on a property based on regular expressions."""
from typing import Union, Tuple, Optional, List, MutableMapping

from aas_core_codegen.common import Error, Identifier
from icontract import ensure

from aas_core_codegen import intermediate
from aas_core_codegen.parse import tree as parse_tree
from aas_core_codegen.infer_for_schema import _common as infer_for_schema_common

# TODO-BEFORE-RELEASE (mristin, 2021-12-13): double-check all the patterns
# Please see the following link for how we construct the regular expressions:
# https://github.com/aas-core-works/abnf-to-regexp/tree/main/test_data/nested-python
_PATTERN_BY_FUNCTION = {
    "is_ID_short": r"^[a-zA-Z][a-zA-Z_0-9]*$",
    "is_MIME": r'([!#$%&\'*+\\-.^_`|~0-9a-zA-Z])+/([!#$%&\'*+\\-.^_`|~0-9a-zA-Z])+([ \t]*;[ \t]*([!#$%&\'*+\\-.^_`|~0-9a-zA-Z])+=(([!#$%&\'*+\\-.^_`|~0-9a-zA-Z])+|"(([\t !#-\\[\\]-~]|[\\x80-\\xff])|\\\\([\t !-~]|[\\x80-\\xff]))*"))*',
}


class PatternConstraint:
    """Constrain a string to comply to a regular expression."""

    def __init__(self, pattern: str) -> None:
        """Initialize with the given values."""
        self.pattern = pattern


class _ConstraintOnProperty:
    """Represent a match on an expression like ``is_ID_short(self.something)``."""

    def __init__(self, prop_name: Identifier, constraint: PatternConstraint) -> None:
        """Initialize with the given values."""
        self.prop_name = prop_name
        self.constraint = constraint


def _match_constraint_on_property(
    node: parse_tree.Node,
) -> Optional[_ConstraintOnProperty]:
    """
    Match the pattern constraints on a property.

    Return the match, or None if not matched.
    """
    if not isinstance(node, parse_tree.FunctionCall):
        return None

    if len(node.args) != 1:
        return None

    prop_name = infer_for_schema_common.match_property(node.args[0])
    if prop_name is None:
        return None

    pattern = _PATTERN_BY_FUNCTION.get(node.name, None)
    if pattern is None:
        return None

    return _ConstraintOnProperty(
        prop_name=prop_name, constraint=PatternConstraint(pattern=pattern)
    )


def infer_pattern_constraints(
    symbol: Union[intermediate.Interface, intermediate.Class]
) -> MutableMapping[intermediate.Property, List[PatternConstraint]]:
    """
    Infer the pattern constraints for every property of the class ``cls``.

    Even if a property is optional, the constraint will still be inferred, since
    schemas usually separate constraints from defining optional/required fields
    (*e.g.*, see JSON schema).

    The constraints are not exhaustive. We only infer constraints based on invariants
    which involve pre-defined list of functions. It might be that the actual invariants
    are tighter.

    The list of patterns means that *all* the patterns need to be satisfied, *i.e.*
    there is a conjunction of patterns.
    """
    constraint_map = dict()  # type: MutableMapping[Identifier, List[PatternConstraint]]

    # NOTE (mristin, 2021-11-30):
    # We iterate only once through the invariants instead of inferring the constraints
    # for each property individually to be able to keep linear time complexity.

    constraints_on_props = []  # type: List[_ConstraintOnProperty]

    for invariant in symbol.parsed.invariants:
        # Match something like ``self.something is None or is_ID_short(self.something)``
        conditional_on_prop = infer_for_schema_common.match_conditional_on_prop(
            invariant.body
        )

        if conditional_on_prop is not None:
            # Match something like
            # ``is_ID_short(self.something) and is_MIME(self.something)``
            if isinstance(conditional_on_prop.consequent, parse_tree.And):
                for value_node in conditional_on_prop.consequent.values:
                    constraint_on_prop = _match_constraint_on_property(value_node)

                    if (
                        constraint_on_prop is not None
                        and constraint_on_prop.prop_name
                        == conditional_on_prop.prop_name
                    ):
                        constraints_on_props.append(constraint_on_prop)

            # Match something like ``is_ID_short(self.something)``
            elif isinstance(conditional_on_prop.consequent, parse_tree.FunctionCall):
                constraint_on_prop = _match_constraint_on_property(
                    node=conditional_on_prop.consequent
                )

                if constraint_on_prop is not None:
                    constraints_on_props.append(constraint_on_prop)

            else:
                # No match
                pass

        else:
            # Match something like
            # ``is_ID_short(self.something) and is_MIME(self.something)``
            if isinstance(invariant.body, parse_tree.And):
                for value_node in invariant.body.values:
                    constraint_on_prop = _match_constraint_on_property(value_node)

                    if constraint_on_prop is not None:
                        constraints_on_props.append(constraint_on_prop)

            # Match something like ``is_ID_short(self.something)``
            elif isinstance(invariant.body, parse_tree.FunctionCall):
                constraint_on_prop = _match_constraint_on_property(node=invariant.body)

                if constraint_on_prop is not None:
                    constraints_on_props.append(constraint_on_prop)

            else:
                # No match
                pass

    # endregion

    # region Group the constraints by property

    result = (
        dict()
    )  # type: MutableMapping[intermediate.Property, List[PatternConstraint]]

    for constraint_on_prop in constraints_on_props:
        prop = symbol.properties_by_name.get(constraint_on_prop.prop_name, None)
        if prop is None:
            continue

        constraints_for_prop = result.get(prop, None)
        if constraints_for_prop is None:
            constraints_for_prop = []
            result[prop] = constraints_for_prop

        constraints_for_prop.append(constraint_on_prop.constraint)

    # endregion

    return result
