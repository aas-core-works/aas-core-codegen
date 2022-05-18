"""Infer constraints representable in common schemas such as JSON Schema or XSD."""

from aas_core_codegen.infer_for_schema import (
    _len,
    _pattern,
    _inline,
    _stringify,
    _types,
)

LenConstraint = _types.LenConstraint
PatternConstraint = _types.PatternConstraint
ConstraintsByProperty = _types.ConstraintsByProperty

infer_constraints_by_class = _inline.infer_constraints_by_class
merge_constraints_with_ancestors = _inline.merge_constraints_with_ancestors

dump = _stringify.dump
