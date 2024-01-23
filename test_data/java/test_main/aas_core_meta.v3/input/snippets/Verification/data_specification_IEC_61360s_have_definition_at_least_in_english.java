/**
 * Check that the {@link IDataSpecificationIec61360#getDefinition() definition} is defined
* for all data specifications whose content is given as IEC 61360 at least in English.
*/
public static boolean dataSpecificationIec61360sHaveDefinitionAtLeastInEnglish(
    Iterable<? extends IEmbeddedDataSpecification> embeddedDataSpecifications){
  for (IEmbeddedDataSpecification embeddedDataSpecification : embeddedDataSpecifications) {
    IDataSpecificationIec61360 iec61360 =
      (IDataSpecificationIec61360) embeddedDataSpecification.getDataSpecificationContent();
    if (iec61360 != null) {
      if (!iec61360.getDefinition().isPresent()) {
        return false;
      }

      boolean noDefinitionInEnglish = true;
      for (ILangStringDefinitionTypeIec61360 langString : iec61360.getDefinition().get()) {
        if (isBcp47ForEnglish(langString.getLanguage())) {
          noDefinitionInEnglish = false;
          break;
        }
      }

      if (noDefinitionInEnglish) {
        return false;
      }
    }
  }
  return true;
}
