/**
* Check that the {@link  IDataSpecificationIec61360#getDataType dataType} is defined
* appropriately for all data specifications whose content is given as IEC 61360.
*/
public static boolean dataSpecificationIec61360sForDocumentHaveAppropriateDataType(
  Iterable<? extends IEmbeddedDataSpecification> embeddedDataSpecifications) {
  Objects.requireNonNull(embeddedDataSpecifications);

  for (IEmbeddedDataSpecification embeddedDataSpecification : embeddedDataSpecifications) {
    IDataSpecificationIec61360 iec61360 =
      (IDataSpecificationIec61360) embeddedDataSpecification.getDataSpecificationContent();
    if(iec61360 != null) {
      if (!iec61360.getDataType().isPresent()
        || !Constants.dataTypeIec61360ForDocument.contains(
           iec61360.getDataType().get())) {
        return false;
      }
    }
  }
  return true;
}
