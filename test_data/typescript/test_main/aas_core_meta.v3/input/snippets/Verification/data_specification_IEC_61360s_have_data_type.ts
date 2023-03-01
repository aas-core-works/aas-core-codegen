/**
 * Check that {@link types.DataSpecificationIec61360.dataType}
 * is defined for all data specifications whose content is given as
 * IEC 61360.
 *
 * @param embeddedDataSpecifications - to be verified
 * @returns `true` if the check passes
 */
export function dataSpecificationIec61360sHaveDataType(
  embeddedDataSpecifications: Iterable<AasTypes.EmbeddedDataSpecification>
): boolean {
  for (const embeddedDataSpecification of embeddedDataSpecifications) {
    const content = embeddedDataSpecification.dataSpecificationContent;
    if (AasTypes.isDataSpecificationIec61360(content)) {
      if (content.dataType === null) {
        return false;
      }
    }
  }

  return true;
}
