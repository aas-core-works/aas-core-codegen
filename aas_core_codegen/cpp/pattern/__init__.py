"""Generate instructions for a virtual machine for matching regular expressions."""

from aas_core_codegen.cpp.pattern import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
