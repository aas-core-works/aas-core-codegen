/**
 * Check that `elements` which are {@link types.Property} or {@link types.Range}
 * have the given `valueType`.
 *
 * @param elements - to be verified
 * @returns `true` if the check passes
 */
export function propertiesOrRangesHaveValueType(
  elements: Iterable<OurTypes.ISubmodelElement>,
  valueType: OurTypes.DataTypeDefXsd
): boolean {
  for (const element of elements) {
    if (OurTypes.isProperty(element) || OurTypes.isRange(element)) {
      if (element.valueType !== valueType) {
        return false;
      }
    }
  }

  return true;
}
