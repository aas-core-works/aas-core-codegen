"""Generate the Golang code for de/serialization of AAS classes from and to JSON."""

from aas_core_codegen.golang.jsonization import _generate

generate = _generate.generate
