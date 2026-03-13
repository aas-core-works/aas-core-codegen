/**
 * Check that {@link types.DataSpecificationIec61360.definition}
 * is defined for all data specifications whose content is given as
 * IEC 61360 at least in English.
 *
 * @param embeddedDataSpecifications - to be verified
 * @returns `true` if the check passes
 */
export function dataSpecificationIec61360sHaveDefinitionAtLeastInEnglish(
  embeddedDataSpecifications: Iterable<AasTypes.EmbeddedDataSpecification>
): boolean {
  for (const embeddedDataSpecification of embeddedDataSpecifications) {
    const content = embeddedDataSpecification.dataSpecificationContent;
    if (AasTypes.isDataSpecificationIec61360(content)) {
      if (content.definition === null) {
        return false;
      }

      let noDefinitionInEnglish = true;
      for (const langString of content.definition) {
        if (isBcp47ForEnglish(langString.language)) {
          noDefinitionInEnglish = false;
          break;
        }
      }

      if (noDefinitionInEnglish === true) {
        return false;
      }
    }
  }

  return true;
}
