// Check that `element` is an instance of the interface corresponding to
// `expectedType`.
func SubmodelElementIsOfType(
	element aastypes.ISubmodelElement,
	expectedType aastypes.AASSubmodelElements,
) bool {
	switch expectedType {
	case aastypes.AASSubmodelElementsAnnotatedRelationshipElement:
		return aastypes.IsAnnotatedRelationshipElement(
			element,
		)
	case aastypes.AASSubmodelElementsBasicEventElement:
		return aastypes.IsBasicEventElement(
			element,
		)
	case aastypes.AASSubmodelElementsBlob:
		return aastypes.IsBlob(
			element,
		)
	case aastypes.AASSubmodelElementsCapability:
		return aastypes.IsCapability(
			element,
		)
	case aastypes.AASSubmodelElementsDataElement:
		return aastypes.IsDataElement(
			element,
		)
	case aastypes.AASSubmodelElementsEntity:
		return aastypes.IsEntity(
			element,
		)
	case aastypes.AASSubmodelElementsEventElement:
		return aastypes.IsEventElement(
			element,
		)
	case aastypes.AASSubmodelElementsFile:
		return aastypes.IsFile(
			element,
		)
	case aastypes.AASSubmodelElementsMultiLanguageProperty:
		return aastypes.IsMultiLanguageProperty(
			element,
		)
	case aastypes.AASSubmodelElementsOperation:
		return aastypes.IsOperation(
			element,
		)
	case aastypes.AASSubmodelElementsProperty:
		return aastypes.IsProperty(
			element,
		)
	case aastypes.AASSubmodelElementsRange:
		return aastypes.IsRange(
			element,
		)
	case aastypes.AASSubmodelElementsReferenceElement:
		return aastypes.IsReferenceElement(
			element,
		)
	case aastypes.AASSubmodelElementsRelationshipElement:
		return aastypes.IsRelationshipElement(
			element,
		)
	case aastypes.AASSubmodelElementsSubmodelElement:
		return aastypes.IsSubmodelElement(
			element,
		)
	case aastypes.AASSubmodelElementsSubmodelElementList:
		return aastypes.IsSubmodelElementList(
			element,
		)
	case aastypes.AASSubmodelElementsSubmodelElementCollection:
		return aastypes.IsSubmodelElementCollection(
			element,
		)
	}
	return false
}
