/// <summary>
/// Check that the <see cref="Aas.IDataSpecificationIec61360.DataType" /> is defined
/// appropriately for all data specifications whose content is given as IEC 61360.
/// </summary>
[CodeAnalysis.SuppressMessage("ReSharper", "InconsistentNaming")]
public static bool DataSpecificationIec61360sForPropertyOrValueHaveAppropriateDataType(
    IEnumerable<Aas.IEmbeddedDataSpecification> embeddedDataSpecifications
)
{
    foreach (var embeddedDataSpecification in embeddedDataSpecifications)
    {
        var iec61360 = (
            embeddedDataSpecification.DataSpecificationContent
                as Aas.IDataSpecificationIec61360
        );
        if (iec61360 != null)
        {
            if (
                iec61360.DataType == null
                || !Constants.DataTypeIec61360ForPropertyOrValue.Contains(
                    iec61360.DataType)
            )
            {
                return false;
            }
        }
    }

    return true;
}