// NOTE (mristin):
// The literals of OurTypes.AasSubmodelElements are consecutive integers starting
// at 0, so we index into an array instead of looking the check up in a map.
const AAS_SUBMODEL_ELEMENTS_TO_IS: ReadonlyArray<
  (that: OurTypes.Class) => boolean
> = [
  OurTypes.isAnnotatedRelationshipElement,
  OurTypes.isBasicEventElement,
  OurTypes.isBlob,
  OurTypes.isCapability,
  OurTypes.isDataElement,
  OurTypes.isEntity,
  OurTypes.isEventElement,
  OurTypes.isFile,
  OurTypes.isMultiLanguageProperty,
  OurTypes.isOperation,
  OurTypes.isProperty,
  OurTypes.isRange,
  OurTypes.isReferenceElement,
  OurTypes.isRelationshipElement,
  OurTypes.isSubmodelElement,
  OurTypes.isSubmodelElementList,
  OurTypes.isSubmodelElementCollection
];

function assertAllTypesCoveredInAasSubmodelElementsToIs() {
  for (const literal of OurTypes.overAasSubmodelElements()) {
    if (AAS_SUBMODEL_ELEMENTS_TO_IS[literal] === undefined) {
      throw new Error(
        `The enumeration literal ${literal} of OurTypes.AasSubmodelElements ` +
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
  element: OurTypes.ISubmodelElement,
  expectedType: OurTypes.AasSubmodelElements
): boolean {
  const isFunc = AAS_SUBMODEL_ELEMENTS_TO_IS[expectedType];
  return isFunc(element);
}
