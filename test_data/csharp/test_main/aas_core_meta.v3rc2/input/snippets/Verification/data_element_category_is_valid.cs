private static readonly HashSet<string> DataElementCategories = new HashSet<string>
{
    "CONSTANT",
    "PARAMETER",
    "VARIABLE"
};

/// <summary>
/// Check that <paramref name="category" /> is a valid
/// category of a data element.
/// </summary>
public static bool DataElementCategoryIsValid(
    string category
)
{
    return DataElementCategories.Contains(
        category);
}
