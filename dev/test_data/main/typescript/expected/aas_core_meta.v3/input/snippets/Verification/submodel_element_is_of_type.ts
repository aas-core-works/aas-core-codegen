const AAS_SUBMODEL_ELEMENTS_TO_IS =
  new Map<AasTypes.AasSubmodelElements, (that: AasTypes.Class) => boolean>(
    [
      [
        AasTypes.AasSubmodelElements.AnnotatedRelationshipElement,
        AasTypes.isAnnotatedRelationshipElement
      ],
      [
        AasTypes.AasSubmodelElements.BasicEventElement,
        AasTypes.isBasicEventElement
      ],
      [
        AasTypes.AasSubmodelElements.Blob,
        AasTypes.isBlob
      ],
      [
        AasTypes.AasSubmodelElements.Capability,
        AasTypes.isCapability
      ],
      [
        AasTypes.AasSubmodelElements.DataElement,
        AasTypes.isDataElement
      ],
      [
        AasTypes.AasSubmodelElements.Entity,
        AasTypes.isEntity
      ],
      [
        AasTypes.AasSubmodelElements.EventElement,
        AasTypes.isEventElement
      ],
      [
        AasTypes.AasSubmodelElements.File,
        AasTypes.isFile
      ],
      [
        AasTypes.AasSubmodelElements.MultiLanguageProperty,
        AasTypes.isMultiLanguageProperty
      ],
      [
        AasTypes.AasSubmodelElements.Operation,
        AasTypes.isOperation
      ],
      [
        AasTypes.AasSubmodelElements.Property,
        AasTypes.isProperty
      ],
      [
        AasTypes.AasSubmodelElements.Range,
        AasTypes.isRange
      ],
      [
        AasTypes.AasSubmodelElements.ReferenceElement,
        AasTypes.isReferenceElement
      ],
      [
        AasTypes.AasSubmodelElements.RelationshipElement,
        AasTypes.isRelationshipElement
      ],
      [
        AasTypes.AasSubmodelElements.SubmodelElement,
        AasTypes.isSubmodelElement
      ],
      [
        AasTypes.AasSubmodelElements.SubmodelElementList,
        AasTypes.isSubmodelElementList
      ],
      [
        AasTypes.AasSubmodelElements.SubmodelElementCollection,
        AasTypes.isSubmodelElementCollection
      ]
    ]);

function assertAllTypesCoveredInAasSubmodelElementsToIs() {
  for (const literal of AasTypes.overAasSubmodelElements()) {
    if (!AAS_SUBMODEL_ELEMENTS_TO_IS.has(literal)) {
      throw new Error(
        `The enumeration literal ${literal} of AasTypes.AasSubmodelElements ` +
          "is not covered in AAS_SUBMODEL_ELEMENTS_TO_IS"
      );
    }
  }
}
assertAllTypesCoveredInAasSubmodelElementsToIs();

/**
 * Check that `element` is an instance of class corresponding to
 * `expectedType`.
 *
 * @param element - to be checked for type
 * @param expectedType - in the check
 * @returns `true` if `element` corresponds to `expectedType`
 */
export function submodelElementIsOfType(
  element: AasTypes.ISubmodelElement,
  expectedType: AasTypes.AasSubmodelElements
): boolean {
  const isFunc = AAS_SUBMODEL_ELEMENTS_TO_IS.get(expectedType);
  return isFunc(element);
}
