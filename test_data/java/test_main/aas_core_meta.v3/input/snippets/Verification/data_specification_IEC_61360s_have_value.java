/** Check that the {@link IDataSpecificationIec61360#getValue() value}  is defined
* for all data specifications whose content is given as IEC 61360.
*/
public static boolean dataSpecificationIec61360sHaveValue(
        Iterable<IEmbeddedDataSpecification> embeddedDataSpecifications
){
    for (IEmbeddedDataSpecification embeddedDataSpecification : embeddedDataSpecifications){
        IDataSpecificationIec61360 iec61360 = (IDataSpecificationIec61360) embeddedDataSpecification.getDataSpecificationContent();
        if (iec61360 != null)
        {
            if (!iec61360.getValue().isPresent())
            {
                return false;
            }
        }
    }
    return true;
}