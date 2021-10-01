"""Generate the C# code for verifying the invariants of the model."""
from aas_core_csharp_codegen.csharp.verification import _generate

verify = _generate.verify
generate = _generate.generate