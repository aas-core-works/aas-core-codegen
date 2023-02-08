/// <summary>
/// Check that the <see cref="Aas.IDataSpecificationIec61360.Value" /> is defined
/// for all data specifications whose content is given as IEC 61360.
/// </summary>
[CodeAnalysis.SuppressMessage("ReSharper", "InconsistentNaming")]
public static bool DataSpecificationIec61360sHaveValue(
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
            if (iec61360.Value == null)
            {
                return false;
            }
        }
    }

    return true;
}
