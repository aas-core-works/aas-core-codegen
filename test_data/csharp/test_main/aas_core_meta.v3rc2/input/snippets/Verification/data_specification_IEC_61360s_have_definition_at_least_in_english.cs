/// <summary>
/// Check that the <see cref="Aas.DataSpecificationIec61360.Definition" /> is defined
/// for all data specifications whose content is given as IEC 61360 at least in English.
/// </summary>
[CodeAnalysis.SuppressMessage("ReSharper", "InconsistentNaming")]
public static bool DataSpecificationIec61360sHaveDefinitionAtLeastInEnglish(
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
            if (iec61360.Definition == null)
            {
                return false;
            }

            foreach (var langString in iec61360.Definition)
            {
                if (IsBcp47ForEnglish(langString.Language))
                {
                    return true;
                }
            }

            return false;
        }
    }

    return true;
}
