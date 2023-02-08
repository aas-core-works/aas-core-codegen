/// <summary>
/// Check that all <see cref="Aas.IExtension.Name" /> are unique among
/// <paramref name="extensions" />.
/// </summary>
public static bool ExtensionNamesAreUnique(
    IEnumerable<Aas.IExtension> extensions
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
