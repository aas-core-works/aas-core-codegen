/// <summary>
/// Return the <see cref="IDataElement.Category" /> or the default value
/// if it has not been set.
/// </summary>
public string CategoryOrDefault()
{
    string result = Category ?? "VARIABLE";

    // TODO: add the post-condition

    return result;
}
