"""Generate C++ functions to de/serialize an instance from XML."""

from aas_core_codegen.cpp.xmlization import _generate

generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
