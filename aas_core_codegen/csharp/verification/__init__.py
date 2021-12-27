"""Generate the C# code for verifying the invariants of the model."""
# pylint: disable=invalid-name

from aas_core_codegen.csharp.verification import _generate

verify = _generate.verify
generate = _generate.generate
