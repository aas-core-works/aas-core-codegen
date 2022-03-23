"""Provide the intermediate representation of the meta-model."""

from aas_core_codegen.intermediate import _types, _translate, _stringify

TypeAnnotation = _types.TypeAnnotation
TypeAnnotationUnion = _types.TypeAnnotationUnion
AtomicTypeAnnotation = _types.AtomicTypeAnnotation
PrimitiveType = _types.PrimitiveType
PrimitiveTypeAnnotation = _types.PrimitiveTypeAnnotation
OurTypeAnnotation = _types.OurTypeAnnotation
ListTypeAnnotation = _types.ListTypeAnnotation
OptionalTypeAnnotation = _types.OptionalTypeAnnotation
SummaryRemarksDescription = _types.SummaryRemarksDescription
SummaryRemarksConstraintsDescription = _types.SummaryRemarksConstraintsDescription
MetaModelDescription = _types.MetaModelDescription
SymbolDescription = _types.SymbolDescription
PropertyDescription = _types.PropertyDescription
EnumerationLiteralDescription = _types.EnumerationLiteralDescription
SignatureDescription = _types.SignatureDescription
DescriptionUnion = _types.DescriptionUnion
Property = _types.Property
Default = _types.Default
DefaultConstant = _types.DefaultConstant
DefaultEnumerationLiteral = _types.DefaultEnumerationLiteral
Argument = _types.Argument
Symbol = _types.Symbol
SymbolExceptEnumeration = _types.SymbolExceptEnumeration
Invariant = _types.Invariant
Contract = _types.Contract
Snapshot = _types.Snapshot
Contracts = _types.Contracts
Method = _types.Method
ImplementationSpecificMethod = _types.ImplementationSpecificMethod
Constructor = _types.Constructor
Serialization = _types.Serialization
ReferenceInTheBook = _types.ReferenceInTheBook
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

type_annotations_equal = _types.type_annotations_equal
beneath_optional = _types.beneath_optional
map_descendability = _types.map_descendability
collect_ids_of_symbols_in_properties = _types.collect_ids_of_symbols_in_properties

translate = _translate.translate
errors_if_contracts_for_functions_or_methods_defined = (
    _translate.errors_if_contracts_for_functions_or_methods_defined
)
errors_if_non_implementation_specific_methods = (
    _translate.errors_if_non_implementation_specific_methods
)

dump = _stringify.dump
