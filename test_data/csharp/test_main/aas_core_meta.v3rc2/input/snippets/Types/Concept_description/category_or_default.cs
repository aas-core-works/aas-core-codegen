/// <summary>
/// Return the <see cref="ConceptDescription.Category" /> or the default value
/// if it has not been set.
/// </summary>
public string CategoryOrDefault()
{
    string result = Category ?? "PROPERTY";

#if DEBUG
    if (!Constants.ValidCategoriesForConceptDescription.Contains(
            result))
    {
        throw new System.InvalidOperationException(
            $"Unexpected default category: {result}"
        );
    }
#endif

    return result;
}
