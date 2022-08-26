/// <summary>
/// Return the <see cref="IReferable.Category" /> or the default value
/// if it has not been set.
/// </summary>
public string CategoryOrDefault()
{
    string result = Category ?? "VARIABLE";

#if DEBUG
    if (!Constants.ValidCategoriesForDataElement.Contains(
            result))
    {
        throw new System.InvalidOperationException(
            $"Unexpected default category: {result}"
        );
    }
#endif

    return result;
}
