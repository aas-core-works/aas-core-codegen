"""Generate C++ code to de/stringify enumerations and primitives."""
from aas_core_codegen.cpp.stringification import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
