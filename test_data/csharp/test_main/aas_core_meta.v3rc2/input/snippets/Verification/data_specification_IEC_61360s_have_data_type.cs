/// <summary>
/// Check that the <see cref="Aas.DataSpecificationIec61360.DataType" /> is defined
/// for all data specifications whose content is given as IEC 61360.
/// </summary>
[CodeAnalysis.SuppressMessage("ReSharper", "InconsistentNaming")]
public static bool DataSpecificationIec61360sHaveDataType(
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
            if (iec61360.DataType == null)
            {
                return false;
            }
        }
    }

    return true;
}
