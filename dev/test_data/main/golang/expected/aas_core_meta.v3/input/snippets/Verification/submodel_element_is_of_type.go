// Check that `element` is an instance of the interface corresponding to
// `expectedType`.
func SubmodelElementIsOfType(
	element ourtypes.ISubmodelElement,
	expectedType ourtypes.AASSubmodelElements,
) bool {
	switch expectedType {
	case ourtypes.AASSubmodelElementsAnnotatedRelationshipElement:
		return ourtypes.IsAnnotatedRelationshipElement(
			element,
		)
	case ourtypes.AASSubmodelElementsBasicEventElement:
		return ourtypes.IsBasicEventElement(
			element,
		)
	case ourtypes.AASSubmodelElementsBlob:
		return ourtypes.IsBlob(
			element,
		)
	case ourtypes.AASSubmodelElementsCapability:
		return ourtypes.IsCapability(
			element,
		)
	case ourtypes.AASSubmodelElementsDataElement:
		return ourtypes.IsDataElement(
			element,
		)
	case ourtypes.AASSubmodelElementsEntity:
		return ourtypes.IsEntity(
			element,
		)
	case ourtypes.AASSubmodelElementsEventElement:
		return ourtypes.IsEventElement(
			element,
		)
	case ourtypes.AASSubmodelElementsFile:
		return ourtypes.IsFile(
			element,
		)
	case ourtypes.AASSubmodelElementsMultiLanguageProperty:
		return ourtypes.IsMultiLanguageProperty(
			element,
		)
	case ourtypes.AASSubmodelElementsOperation:
		return ourtypes.IsOperation(
			element,
		)
	case ourtypes.AASSubmodelElementsProperty:
		return ourtypes.IsProperty(
			element,
		)
	case ourtypes.AASSubmodelElementsRange:
		return ourtypes.IsRange(
			element,
		)
	case ourtypes.AASSubmodelElementsReferenceElement:
		return ourtypes.IsReferenceElement(
			element,
		)
	case ourtypes.AASSubmodelElementsRelationshipElement:
		return ourtypes.IsRelationshipElement(
			element,
		)
	case ourtypes.AASSubmodelElementsSubmodelElement:
		return ourtypes.IsSubmodelElement(
			element,
		)
	case ourtypes.AASSubmodelElementsSubmodelElementList:
		return ourtypes.IsSubmodelElementList(
			element,
		)
	case ourtypes.AASSubmodelElementsSubmodelElementCollection:
		return ourtypes.IsSubmodelElementCollection(
			element,
		)
	}
	return false
}
