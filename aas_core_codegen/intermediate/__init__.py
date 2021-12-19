"""Provide the intermediate representation of the meta-model."""

# pylint: disable=invalid-name

from aas_core_codegen.intermediate import _types, _translate, _stringify

TypeAnnotation = _types.TypeAnnotation
AtomicTypeAnnotation = _types.AtomicTypeAnnotation
BuiltinAtomicType = _types.BuiltinAtomicType
BuiltinAtomicTypeAnnotation = _types.BuiltinAtomicTypeAnnotation
OurAtomicTypeAnnotation = _types.OurAtomicTypeAnnotation
SubscriptedTypeAnnotation = _types.SubscriptedTypeAnnotation
ListTypeAnnotation = _types.ListTypeAnnotation
OptionalTypeAnnotation = _types.OptionalTypeAnnotation
RefTypeAnnotation = _types.RefTypeAnnotation
Description = _types.Description
Property = _types.Property
Default = _types.Default
DefaultConstant = _types.DefaultConstant
DefaultEnumerationLiteral = _types.DefaultEnumerationLiteral
Argument = _types.Argument
Signature = _types.Signature
Symbol = _types.Symbol
Interface = _types.Interface
Invariant = _types.Invariant
Contract = _types.Contract
Snapshot = _types.Snapshot
Contracts = _types.Contracts
Method = _types.Method
Constructor = _types.Constructor
Serialization = _types.Serialization
EnumerationLiteral = _types.EnumerationLiteral
Enumeration = _types.Enumeration
Class = _types.Class
SymbolTable = _types.SymbolTable
SymbolReferenceInDoc = _types.SymbolReferenceInDoc
PropertyReferenceInDoc = _types.PropertyReferenceInDoc
EnumerationLiteralReferenceInDoc = _types.EnumerationLiteralReferenceInDoc
AttributeReferenceInDoc = _types.AttributeReferenceInDoc

InterfaceImplementers = _types.InterfaceImplementers
map_interface_implementers = _types.map_interface_implementers
map_descendability = _types.map_descendability
make_union_of_constructor_arguments = _types.make_union_of_constructor_arguments
collect_ids_of_interfaces_in_properties = _types.collect_ids_of_interfaces_in_properties

translate = _translate.translate

dump = _stringify.dump
