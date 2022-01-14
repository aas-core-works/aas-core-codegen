"""Infer constraints representable in common schemas such as JSON Schema or XSD."""

from aas_core_codegen.infer_for_schema import _len, _pattern, _stringify

LenConstraint = _len.LenConstraint
infer_len_constraints_by_class_properties = (
    _len.infer_len_constraints_by_class_properties
)
infer_len_constraint_of_self = _len.infer_len_constraint_of_self

PatternConstraint = _pattern.PatternConstraint
infer_patterns_by_class_properties = _pattern.infer_patterns_by_class_properties
infer_patterns_on_self = _pattern.infer_patterns_on_self
PatternVerificationsByName = _pattern.PatternVerificationsByName
map_pattern_verifications_by_name = _pattern.map_pattern_verifications_by_name

dump = _stringify.dump
dump_len_constraints_by_properties = _stringify.dump_len_constraints_by_properties
dump_patterns = _stringify.dump_patterns
dump_patterns_by_properties = _stringify.dump_patterns_by_properties
