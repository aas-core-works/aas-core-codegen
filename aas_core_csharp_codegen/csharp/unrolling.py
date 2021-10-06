"""Provide common functionalities for unrolling recursive calls and iterations."""
import io
import textwrap
from typing import Sequence

from aas_core_csharp_codegen.csharp import (common as csharp_common)


class Node:
    """Represent a node in the unrolling tree."""

    def __init__(self, text: str, children: Sequence['Node']):
        self.text = text
        self.children = children


def render(node: Node) -> str:
    """
    Render the node recursively.

    >>> render(Node(text='something', children=[]))
    'something'

    >>> render(Node(text='parent', children=[Node(text='child', children=[])]))
    'parent\\n{\\n    child\\n}'
    """
    if len(node.children) == 0:
        return node.text

    writer = io.StringIO()
    writer.write(node.text)
    writer.write('\n{')

    for i, child in enumerate(node.children):
        if i == 0:
            writer.write('\n')
        else:
            writer.write('\n\n')

        writer.write(textwrap.indent(render(child), csharp_common.INDENT))

    writer.write('\n}')

    return writer.getvalue()
