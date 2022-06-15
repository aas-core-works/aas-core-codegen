"""
Parse and operate on regular expressions defined over a possibly-formatted string.

Due to time constraints, we do not handle the whole of Python regular expression,
but just a subset. This subset was exactly enough to handle all the expressions of the
current meta-models. With newer meta-models, the subset is expected to grow.
"""

from aas_core_codegen.parse.retree import _parse, _types, _stringify, _render, _visitor

parse = _parse.parse
Error = _parse.Error
Cursor = _parse.Cursor
render_pointer = _parse.render_pointer

Char = _types.Char
Range = _types.Range
Concatenation = _types.Concatenation
SymbolKind = _types.SymbolKind
Symbol = _types.Symbol
Group = _types.Group
CharSet = _types.CharSet
Quantifier = _types.Quantifier
Term = _types.Term
UnionExpr = _types.UnionExpr
Regex = _types.Regex
TermValueUnion = _types.TermValueUnion
Visitor = _types.Visitor
Transformer = _types.Transformer

BaseVisitor = _visitor.BaseVisitor

dump = _stringify.dump

render = _render.render
