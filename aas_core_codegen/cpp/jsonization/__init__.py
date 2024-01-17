"""Generate C++ functions to de/serialize an instance from a JSON value."""

from aas_core_codegen.cpp.jsonization import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
