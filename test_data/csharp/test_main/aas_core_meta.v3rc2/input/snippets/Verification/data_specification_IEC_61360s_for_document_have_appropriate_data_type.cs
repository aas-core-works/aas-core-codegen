/// <summary>
/// Check that the <see cref="Aas.DataSpecificationIec61360.DataType" /> is defined
/// appropriately for all data specifications whose content is given as IEC 61360.
/// </summary>
[CodeAnalysis.SuppressMessage("ReSharper", "InconsistentNaming")]
public static bool DataSpecificationIec61360sForDocumentHaveAppropriateDataType(
    IEnumerable<Aas.EmbeddedDataSpecification> embeddedDataSpecifications
)
{
    foreach (var embeddedDataSpecification in embeddedDataSpecifications)
    {
        var iec61360 = (
            embeddedDataSpecification.DataSpecificationContent
                as DataSpecificationIec61360
        );
        if (iec61360 != null)
        {
            if (
                iec61360.DataType == null
                || !Constants.DataTypeIec61360ForDocument.Contains(
                    iec61360.DataType)
            )
            {
                return false;
            }
        }
    }

    return true;
}
