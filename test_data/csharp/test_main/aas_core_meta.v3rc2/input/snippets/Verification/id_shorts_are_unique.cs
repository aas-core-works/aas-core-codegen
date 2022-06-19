/// <summary>
/// Check that all <see cref="Aas.IReferable.IdShort" /> are unique among
/// <paramref name="referables" />.
/// </summary>
public static bool IdShortsAreUnique(
    IEnumerable<Aas.IReferable> referables
)
{
    var idShortSet = new HashSet<string>();
    foreach (var referable in referables)
    {
        if (referable.IdShort != null)
        {
            if (idShortSet.Contains(referable.IdShort))
            {
                return false;
            }
            idShortSet.Add(referable.IdShort);
        }
    }
    return true;
}
