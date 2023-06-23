"""Generate the Golang code for verifying the invariants of the model."""

from aas_core_codegen.golang.verification import _generate

verify = _generate.verify
generate = _generate.generate
