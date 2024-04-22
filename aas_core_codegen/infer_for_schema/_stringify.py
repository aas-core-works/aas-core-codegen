"""Represent inferred constraints as strings."""

import collections
from typing import Union, Optional

from aas_core_codegen import stringify, intermediate
from aas_core_codegen.infer_for_schema._types import (
    LenConstraint,
    PatternConstraint,
    ConstraintsByProperty,
    SetOfPrimitivesConstraint,
    SetOfEnumerationLiteralsConstraint,
)


def _stringify_len_constraint(
    that: LenConstraint,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("min_value", that.min_value),
            stringify.Property("max_value", that.max_value),
        ],
    )

    return result


def _stringify_pattern_constraint(
    that: PatternConstraint,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("pattern", that.pattern),
        ],
    )

    return result


def _stringify_set_of_primitives_constraint(
    that: SetOfPrimitivesConstraint,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property("a_type", that.a_type.name),
            stringify.Property(
                "literals", list(map(intermediate.stringify, that.literals))
            ),
        ],
    )

    return result


def _stringify_set_of_enumeration_literals_constraint(
    that: SetOfEnumerationLiteralsConstraint,
) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property(
                "enumeration",
                f"Reference to {that.enumeration.__class__.__name__} "
                f"{that.enumeration.name}",
            ),
            stringify.Property(
                "literals",
                [
                    f"Reference to {literal.__class__.__name__} {literal.name}"
                    for literal in that.literals
                ],
            ),
        ],
    )

    return result


def _stringify_constraints_by_property(that: ConstraintsByProperty) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property(
                "len_constraints_by_property",
                # fmt: off
                collections.OrderedDict(
                    [
                        # NOTE (mristin, 2022-05-18):
                        # Mypy could not infer that an identifier is also a string.
                        # Hence, we need to explicitly convert to a str here.
                        (str(prop.name), _stringify_len_constraint(len_constraint))
                        for prop, len_constraint in
                        that.len_constraints_by_property.items()
                    ]
                ),
                # fmt: on
            ),
            stringify.Property(
                "patterns_by_property",
                # fmt: off
                collections.OrderedDict(
                    [
                        (
                            # NOTE (mristin, 2022-05-18):
                            # Mypy could not infer that an identifier is also a string.
                            # Hence, we need to explicitly convert to a str here.
                            str(prop.name),
                            [_stringify(pattern) for pattern in patterns],
                        )
                        for prop, patterns in that.patterns_by_property.items()
                    ]
                ),
                # fmt: on
            ),
            stringify.Property(
                "set_of_primitives_by_property",
                # fmt: off
                collections.OrderedDict(
                    [
                        # NOTE (mristin, 2022-07-08):
                        # Mypy could not infer that an identifier is also a string.
                        # Hence, we need to explicitly convert to a str here.
                        (str(prop.name), _stringify(set_of_primitives))
                        for prop, set_of_primitives in
                        that.set_of_primitives_by_property.items()
                    ]
                ),
                # fmt: on
            ),
            stringify.Property(
                "set_of_enumeration_literals_by_property",
                # fmt: off
                collections.OrderedDict(
                    [
                        # NOTE (mristin, 2022-07-08):
                        # Mypy could not infer that an identifier is also a string.
                        # Hence, we need to explicitly convert to a str here.
                        (str(prop.name), _stringify(set_of_enum_literals))
                        for prop, set_of_enum_literals in
                        that.set_of_enumeration_literals_by_property.items()
                    ]
                ),
                # fmt: on
            ),
        ],
    )

    return result


Dumpable = Union[
    LenConstraint,
    PatternConstraint,
    SetOfPrimitivesConstraint,
    SetOfEnumerationLiteralsConstraint,
    ConstraintsByProperty,
]

_DISPATCH = {
    LenConstraint: _stringify_len_constraint,
    PatternConstraint: _stringify_pattern_constraint,
    SetOfPrimitivesConstraint: _stringify_set_of_primitives_constraint,
    # fmt: off
    SetOfEnumerationLiteralsConstraint: (
        _stringify_set_of_enumeration_literals_constraint
    ),
    # fmt: on
    ConstraintsByProperty: _stringify_constraints_by_property,
}

stringify.assert_dispatch_exhaustive(dispatch=_DISPATCH, dumpable=Dumpable)


def _stringify(that: Optional[Dumpable]) -> Optional[stringify.Entity]:
    """Dispatch to the correct ``_stringify_*`` method."""
    if that is None:
        return None

    stringify_func = _DISPATCH.get(that.__class__, None)
    if stringify_func is None:
        raise AssertionError(
            f"No stringify function could be found for the class {that.__class__}"
        )

    stringified = stringify_func(that)  # type: ignore
    assert isinstance(stringified, stringify.Entity)
    stringify.assert_compares_against_dict(stringified, that)

    return stringified


def dump(that: Optional[Dumpable]) -> str:
    """Produce a string representation of the ``dumpable`` for testing or debugging."""
    if that is None:
        return repr(None)

    stringified = _stringify(that)
    return stringify.dump(stringified)
