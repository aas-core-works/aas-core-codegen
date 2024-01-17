"""Generate C++ functions to iterate over the instances."""

from aas_core_codegen.cpp.iteration import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
