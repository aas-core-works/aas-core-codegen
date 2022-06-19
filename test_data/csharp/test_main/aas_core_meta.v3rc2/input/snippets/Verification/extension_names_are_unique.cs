/// <summary>
/// Check that all <see cref="Aas.Extension.Name" /> are unique among
/// <paramref name="extensions" />.
/// </summary>
public static bool ExtensionNamesAreUnique(
    IEnumerable<Aas.Extension> extensions
)
{
    var nameSet = new HashSet<string>();
    foreach (var extension in extensions)
    {
        if (nameSet.Contains(extension.Name))
        {
            return false;
        }
        nameSet.Add(extension.Name);
    }
    return true;
}
