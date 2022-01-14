"""Represent inferred constraints as strings."""
import io
import textwrap
from typing import Union, Optional, Mapping, Sequence

from aas_core_codegen import stringify, intermediate
from aas_core_codegen.infer_for_schema._len import LenConstraint
from aas_core_codegen.infer_for_schema._pattern import PatternConstraint


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


Dumpable = Union[LenConstraint, PatternConstraint]

_DISPATCH = {
    LenConstraint: _stringify_len_constraint,
    PatternConstraint: _stringify_pattern_constraint,
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


def dump_len_constraints_by_properties(
    that: Optional[Mapping[intermediate.Property, LenConstraint]]
) -> str:
    """Represent the map of constraints by properties as strings."""
    if that is None:
        return repr(None)

    if len(that) == 0:
        return "{}"

    writer = io.StringIO()
    writer.write("{\n")
    for i, (prop, dumpable) in enumerate(that.items()):
        writer.write(f"  {prop.name!r}:\n")
        writer.write(textwrap.indent(dump(dumpable), "  "))

        if i < len(that) - 1:
            writer.write(",")

        writer.write("\n")

    writer.write("}")
    return writer.getvalue()


def dump_patterns(that: Optional[Sequence[PatternConstraint]]) -> str:
    """Represent the sequence of patterns as a string."""
    if that is None:
        return repr(None)

    writer = io.StringIO()

    if len(that) == 0:
        writer.write("[]")
    else:
        writer.write("[\n")
        for pattern_i, pattern in enumerate(that):
            writer.write(textwrap.indent(dump(pattern), "  "))

            if pattern_i < len(that) - 1:
                writer.write(",")

            writer.write("\n")

        writer.write("]")

    return writer.getvalue()


def dump_patterns_by_properties(
    that: Optional[Mapping[intermediate.Property, Sequence[PatternConstraint]]]
) -> str:
    """Represent the map of patterns by properties as strings."""
    if that is None:
        return repr(None)

    if len(that) == 0:
        return "{}"

    writer = io.StringIO()
    writer.write("{\n")
    for i, (prop, patterns) in enumerate(that.items()):
        writer.write(f"  {prop.name!r}:\n")
        writer.write(textwrap.indent(dump_patterns(patterns), "  "))

        if i < len(that) - 1:
            writer.write(",")

        writer.write("\n")

    writer.write("}")
    return writer.getvalue()
