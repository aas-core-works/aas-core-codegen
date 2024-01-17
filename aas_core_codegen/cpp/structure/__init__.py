"""Generate C++ data structures to represent, iterate and transform an."""

from aas_core_codegen.cpp.structure import _generate

verify = _generate.verify
generate_header = _generate.generate_header
generate_implementation = _generate.generate_implementation
