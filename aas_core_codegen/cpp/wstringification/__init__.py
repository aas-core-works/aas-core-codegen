"""Generate C++ code to de/wstringify enumerations and primitives."""

from aas_core_codegen.cpp.wstringification import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
