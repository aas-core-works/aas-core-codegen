/// <summary>
/// Check that the target of the model <paramref name="reference" /> matches
/// a <see cref="Aas.Constants.AasReferables" />.
/// </summary>
public static bool IsModelReferenceToReferable(
    Aas.Reference reference
)
{
    if (reference.Type != Aas.ReferenceTypes.ModelReference)
    {
        return false;
    }

    if (reference.Keys.Count == 0)
    {
        return false;
    }

    return Aas.Constants.AasReferables.Contains(reference.Keys[^1].Type);
}
