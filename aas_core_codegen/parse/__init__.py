"""Parse the meta model."""
from typing import Tuple, Optional

import asttokens

from aas_core_codegen.parse import _types, _translate, _stringify

TypeAnnotation = _types.TypeAnnotation
AtomicTypeAnnotation = _types.AtomicTypeAnnotation
SelfTypeAnnotation = _types.SelfTypeAnnotation
SubscriptedTypeAnnotation = _types.SubscriptedTypeAnnotation
Description = _types.Description
Property = _types.Property
Default = _types.Default
Argument = _types.Argument
Invariant = _types.Invariant
Contract = _types.Contract
Snapshot = _types.Snapshot
Contracts = _types.Contracts
is_string_expr = _types.is_string_expr
ImplementationSpecificMethod = _types.ImplementationSpecificMethod
UnderstoodMethod = _types.UnderstoodMethod
ConstructorToBeUnderstood = _types.ConstructorToBeUnderstood
Method = _types.Method
MethodUnion = _types.MethodUnion
FunctionUnion = _types.FunctionUnion
Symbol = _types.Symbol
Serialization = _types.Serialization
ReferenceInTheBook = _types.ReferenceInTheBook
Class = _types.Class
AbstractClass = _types.AbstractClass
ClassUnion = _types.ClassUnion
ConcreteClass = _types.ConcreteClass
EnumerationLiteral = _types.EnumerationLiteral
Enumeration = _types.Enumeration
MetaModel = _types.MetaModel
SymbolTable = _types.SymbolTable

PRIMITIVE_TYPES = _types.PRIMITIVE_TYPES
GENERIC_TYPES = _types.GENERIC_TYPES

source_to_atok = _translate.source_to_atok
check_expected_imports = _translate.check_expected_imports
atok_to_symbol_table = _translate.atok_to_symbol_table

dump = _stringify.dump

# BEFORE-RELEASE (mristin, 2021-12-13):
#  integrate __book_version__ and __book_url__ into parsed and intermediate types,
#  and add them to comments in the generated code

# BEFORE-RELEASE (mristin, 2021-12-13):
#  parse markers reference_in_the_book and integrate them in the generated code

# BEFORE-RELEASE (mristin, 2021-12-13):
#  handle constrained primitive types
