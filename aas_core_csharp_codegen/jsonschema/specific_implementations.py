"""Handle specific implementations for JSON schemas."""

import pathlib
from typing import Optional, List, Tuple

from icontract import ensure

from aas_core_csharp_codegen.common import Stripped
from aas_core_csharp_codegen.specific_implementations import SpecificImplementations, \
    ImplementationKey, IMPLEMENTATION_KEY_RE


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def read_from_directory(
        snippets_dir: pathlib.Path
) -> Tuple[Optional[SpecificImplementations], Optional[List[str]]]:
    """
    Read all the implementation-specific code snippets from the ``snippets_dir``.

    All the snippet files are expected to have the extension ``.schema.json``.

    :return: either the map of the implementations, or the errors
    """
    mapping = dict()

    errors = []  # type: List[str]
    for pth in snippets_dir.glob("**/*"):
        if pth.is_dir():
            continue

        if not pth.name.endswith(".schema.json"):
            errors.append(
                f"Expected only *.schema.json files in the implementations, "
                f"but got: {pth}")
            continue

        stem = pth.name[:-len(".schema.json")]

        maybe_key = (pth.relative_to(snippets_dir).parent / stem).as_posix()
        if not IMPLEMENTATION_KEY_RE.match(maybe_key):
            errors.append(
                f"The snippet key is not valid "
                f"according to {IMPLEMENTATION_KEY_RE.pattern}: {maybe_key}")
            continue

        key = ImplementationKey(maybe_key)
        value = Stripped(pth.read_text().strip())
        mapping[key] = value

    if errors:
        return None, errors

    return mapping, None
