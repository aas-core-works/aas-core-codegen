"""Parse the meta model."""
from typing import Tuple, Optional

import asttokens

from aas_core_csharp_codegen.parse import _types, _translate, _stringify

# pylint: disable=invalid-name

TypeAnnotation = _types.TypeAnnotation
AtomicTypeAnnotation = _types.AtomicTypeAnnotation
SelfTypeAnnotation = _types.SelfTypeAnnotation
SubscriptedTypeAnnotation = _types.SubscriptedTypeAnnotation
final_in_type_annotation = _types.final_in_type_annotation
Property = _types.Property
Default = _types.Default
Argument = _types.Argument
Contract = _types.Contract
Snapshot = _types.Snapshot
Contracts = _types.Contracts
is_string_expr = _types.is_string_expr
Method = _types.Method
Symbol = _types.Symbol
Entity = _types.Entity
AbstractEntity = _types.AbstractEntity
ConcreteEntity = _types.ConcreteEntity
EnumerationLiteral = _types.EnumerationLiteral
Enumeration = _types.Enumeration
SymbolTable = _types.SymbolTable

BUILTIN_ATOMIC_TYPES = _types.BUILTIN_ATOMIC_TYPES
BUILTIN_COMPOSITE_TYPES = _types.BUILTIN_COMPOSITE_TYPES

source_to_atok = _translate.source_to_atok
check_expected_imports = _translate.check_expected_imports
atok_to_symbol_table = _translate.atok_to_symbol_table

dump = _stringify.dump
