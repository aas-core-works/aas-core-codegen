"""Infer constraints representable in common schemas such as JSON Schema or XSD."""

from aas_core_codegen.infer_for_schema import (
    match,
    _len,
    _pattern,
    _inline,
    _stringify,
    _types,
)

# TODO: clean up and look for usage

LenConstraint = _types.LenConstraint
PatternConstraint = _types.PatternConstraint
SetOfPrimitivesConstraint = _types.SetOfPrimitivesConstraint
SetOfEnumerationLiteralsConstraint = _types.SetOfEnumerationLiteralsConstraint

Constraints = _types.Constraints
ConstraintsByValue = _types.ConstraintsByValue

infer_constraints_by_class = _inline.infer_constraints_by_class

# TODO: remove this one once refactored
merge_constraints_with_ancestors = _inline.merge_constraints_with_ancestors

dump = _stringify.dump
