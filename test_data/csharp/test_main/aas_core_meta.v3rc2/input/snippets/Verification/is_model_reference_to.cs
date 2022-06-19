/// <summary>
/// Check that the target of the model <paramref name="reference" /> matches
/// the <paramref name="expectedType" />.
/// </summary>
public static bool IsModelReferenceTo(
    Aas.Reference reference,
    Aas.KeyTypes expectedType
)
{
    if (reference.Keys.Count == 0)
    {
        return false;
    }

    return reference.Keys[^1].Type == expectedType;
}
