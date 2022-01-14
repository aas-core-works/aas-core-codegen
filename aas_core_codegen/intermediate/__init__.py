"""Provide the intermediate representation of the meta-model."""

from aas_core_codegen.intermediate import _types, _translate, _stringify

TypeAnnotation = _types.TypeAnnotation
TypeAnnotationUnion = _types.TypeAnnotationUnion
PrimitiveType = _types.PrimitiveType
PrimitiveTypeAnnotation = _types.PrimitiveTypeAnnotation
OurTypeAnnotation = _types.OurTypeAnnotation
ListTypeAnnotation = _types.ListTypeAnnotation
OptionalTypeAnnotation = _types.OptionalTypeAnnotation
RefTypeAnnotation = _types.RefTypeAnnotation
Description = _types.Description
Property = _types.Property
Default = _types.Default
DefaultConstant = _types.DefaultConstant
DefaultEnumerationLiteral = _types.DefaultEnumerationLiteral
Argument = _types.Argument
Symbol = _types.Symbol
Invariant = _types.Invariant
Contract = _types.Contract
Snapshot = _types.Snapshot
Contracts = _types.Contracts
Method = _types.Method
ImplementationSpecificMethod = _types.ImplementationSpecificMethod
Constructor = _types.Constructor
Serialization = _types.Serialization
EnumerationLiteral = _types.EnumerationLiteral
Enumeration = _types.Enumeration
ConstrainedPrimitive = _types.ConstrainedPrimitive
Class = _types.Class
ClassUnion = _types.ClassUnion
ConcreteClass = _types.ConcreteClass
AbstractClass = _types.AbstractClass
Verification = _types.Verification
ImplementationSpecificVerification = _types.ImplementationSpecificVerification
PatternVerification = _types.PatternVerification
Signature = _types.Signature
Interface = _types.Interface
SymbolTable = _types.SymbolTable

map_descendability = _types.map_descendability
make_union_of_constructor_arguments = _types.make_union_of_constructor_arguments
collect_ids_of_classes_in_properties = _types.collect_ids_of_classes_in_properties

translate = _translate.translate
errors_if_contracts_for_functions_or_methods_defined = (
    _translate.errors_if_contracts_for_functions_or_methods_defined
)
errors_if_non_implementation_specific_methods = (
    _translate.errors_if_non_implementation_specific_methods
)

dump = _stringify.dump
