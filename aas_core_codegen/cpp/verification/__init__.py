"""Generate C++ functions to verify an instance."""

from aas_core_codegen.cpp.verification import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
