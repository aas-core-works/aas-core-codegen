"""Provide parsing functions to get started with testing some of the ReST rendering."""
import io
from typing import Optional

import docutils.nodes
import docutils.core


def parse_restructured_text(text: str) -> docutils.nodes.document:
    """Parse the given ReST ``text``."""
    warnings = io.StringIO()
    document = None  # type: Optional[docutils.nodes.document]

    document = docutils.core.publish_doctree(
        text, settings_overrides={"warning_stream": warnings}
    )

    warnings_text = warnings.getvalue()
    if warnings_text:
        raise RuntimeError(
            f"Failed to parse the description with docutils:\n{warnings_text.strip()}"
        )

    assert document is not None

    return document
