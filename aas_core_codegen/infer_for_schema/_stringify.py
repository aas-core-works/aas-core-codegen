"""Represent inferred constraints as strings."""
import collections
from typing import Union, Optional

from aas_core_codegen import stringify
from aas_core_codegen.infer_for_schema._types import (
    LenConstraint,
    PatternConstraint,
    ConstraintsByProperty,
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


def _stringify_constraints_by_property(that: ConstraintsByProperty) -> stringify.Entity:
    result = stringify.Entity(
        name=that.__class__.__name__,
        properties=[
            stringify.Property(
                "len_constraints_by_property",
                collections.OrderedDict(
                    [
                        # NOTE (mristin, 2022-05-18):
                        # Mypy could not infer that an identifier is also a string.
                        # Hence we need to explicitly convert to a str here.
                        (str(prop.name), _stringify_len_constraint(len_constraint))
                        for prop, len_constraint in that.len_constraints_by_property.items()
                    ]
                ),
            ),
            stringify.Property(
                "patterns_by_property",
                collections.OrderedDict(
                    [
                        (
                            # NOTE (mristin, 2022-05-18):
                            # Mypy could not infer that an identifier is also a string.
                            # Hence we need to explicitly convert to a str here.
                            str(prop.name),
                            [
                                _stringify_pattern_constraint(pattern_constraint)
                                for pattern_constraint in pattern_constraints
                            ],
                        )
                        for prop, pattern_constraints in that.patterns_by_property.items()
                    ]
                ),
            ),
        ],
    )

    return result


Dumpable = Union[LenConstraint, PatternConstraint, ConstraintsByProperty]

_DISPATCH = {
    LenConstraint: _stringify_len_constraint,
    PatternConstraint: _stringify_pattern_constraint,
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
