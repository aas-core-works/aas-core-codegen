"""Infer constraints representable in common schemas such as JSON Schema or XSD."""

from aas_core_codegen.infer_for_schema import _len, _pattern

LenConstraint = _len.LenConstraint
infer_len_constraints = _len.infer_len_constraints

PatternConstraint = _pattern.PatternConstraint
infer_pattern_constraints = _pattern.infer_pattern_constraints
