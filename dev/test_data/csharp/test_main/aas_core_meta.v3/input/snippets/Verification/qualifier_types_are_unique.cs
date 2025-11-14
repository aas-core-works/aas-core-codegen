/// <summary>
/// Check that there are no duplicate <see cref="Aas.IQualifier.Type" />'s
/// in the <paramref name="qualifiers" />.
/// </summary>
public static bool QualifierTypesAreUnique(
    IEnumerable<Aas.IQualifier> qualifiers
)
{
    var typeSet = new HashSet<string>();
    foreach (var qualifier in qualifiers)
    {
        if (typeSet.Contains(qualifier.Type))
        {
            return false;
        }
        typeSet.Add(qualifier.Type);
    }
    return true;
}
