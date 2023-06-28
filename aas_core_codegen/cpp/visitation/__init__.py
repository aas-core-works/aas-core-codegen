"""Generate C++ visitors to iterate over instances."""

from aas_core_codegen.cpp.visitation import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
