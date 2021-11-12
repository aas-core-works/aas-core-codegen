"""Provide common functions for both RDF and SHACL generators."""
from aas_core_csharp_codegen.common import Stripped


def string_literal(text: str) -> Stripped:
    """Generate a valid and escaped string literal based on the free-form ``text``."""
    if len(text) == 0:
        return Stripped('""')

    escaped = text.replace('"', '\\"')
    if '\n' in escaped:
        return Stripped(f'"""{escaped}"""')
    else:
        return Stripped(f'"{escaped}"')
