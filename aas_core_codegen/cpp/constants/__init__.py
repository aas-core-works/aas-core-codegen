"""Generate C++ constants corresponding to the constants of the meta-model."""

from aas_core_codegen.cpp.constants import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
