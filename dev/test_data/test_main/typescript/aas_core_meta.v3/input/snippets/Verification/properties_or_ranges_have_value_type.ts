/**
 * Check that `elements` which are {@link types.Property} or {@link types.Range}
 * have the given `valueType`.
 *
 * @param elements - to be verified
 * @returns `true` if the check passes
 */
export function propertiesOrRangesHaveValueType(
  elements: Iterable<AasTypes.ISubmodelElement>,
  valueType: AasTypes.DataTypeDefXsd
): boolean {
  for (const element of elements) {
    if (AasTypes.isProperty(element) || AasTypes.isRange(element)) {
      if (element.valueType !== valueType) {
        return false;
      }
    }
  }

  return true;
}
