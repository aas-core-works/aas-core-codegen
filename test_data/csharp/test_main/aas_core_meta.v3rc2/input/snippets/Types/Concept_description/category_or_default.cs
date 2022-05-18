/// <summary>
/// Return the <see cref="Aas.ConceptDescription.Category" /> or the default value
/// if it has not been set.
/// </summary>
public string CategoryOrDefault()
{
    string result = (this.category != null)
        ? this.category
        : "PROPERTY";

#if DEBUG
    if (!Verification.ConceptDescriptionCategoryIsValid(
            result))
    {
        throw new System.InvalidOperationException(
            $"Unexpected default category: {result}"
        );
    }
#endif
}
