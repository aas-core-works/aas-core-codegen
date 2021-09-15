"""Provide the intermediate representation of the meta-model."""

# pylint: disable=invalid-name

from aas_core_csharp_codegen.intermediate import _types, _translate, _stringify

TypeAnnotation = _types.TypeAnnotation
AtomicTypeAnnotation = _types.AtomicTypeAnnotation
BuiltinAtomicType = _types.BuiltinAtomicType
BuiltinAtomicTypeAnnotation = _types.BuiltinAtomicTypeAnnotation
OurAtomicTypeAnnotation = _types.OurAtomicTypeAnnotation
SelfTypeAnnotation = _types.SelfTypeAnnotation
SubscriptedTypeAnnotation = _types.SubscriptedTypeAnnotation
ListTypeAnnotation = _types.ListTypeAnnotation
SequenceTypeAnnotation = _types.SequenceTypeAnnotation
SetTypeAnnotation = _types.SetTypeAnnotation
MappingTypeAnnotation = _types.MappingTypeAnnotation
MutableMappingTypeAnnotation = _types.MutableMappingTypeAnnotation
OptionalTypeAnnotation = _types.OptionalTypeAnnotation
Property = _types.Property
Default = _types.Default
Argument = _types.Argument
Signature = _types.Signature
Symbol = _types.Symbol
Interface = _types.Interface
Contract = _types.Contract
Snapshot = _types.Snapshot
Contracts = _types.Contracts
Method = _types.Method
Constructor = _types.Constructor
EnumerationLiteral = _types.EnumerationLiteral
Enumeration = _types.Enumeration
Class = _types.Class
SymbolTable = _types.SymbolTable

translate = _translate.translate

dump = _stringify.dump
