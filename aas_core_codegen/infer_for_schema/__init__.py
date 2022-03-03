"""Infer constraints representable in common schemas such as JSON Schema or XSD."""

from aas_core_codegen.infer_for_schema import _len, _pattern, _inline, _stringify

LenConstraint = _len.LenConstraint

PatternConstraint = _pattern.PatternConstraint

ConstraintsByProperty = _inline.ConstraintsByProperty
infer_constraints_by_class = _inline.infer_constraints_by_class

dump = _stringify.dump
dump_len_constraints_by_properties = _stringify.dump_len_constraints_by_properties
dump_patterns = _stringify.dump_patterns
dump_patterns_by_properties = _stringify.dump_patterns_by_properties
