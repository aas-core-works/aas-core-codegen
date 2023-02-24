/// <summary>
/// Check that the two references, <paramref name="that" /> and
/// <paramref name="other" />, are equal by comparing
/// their <see cref="Aas.IReference.Keys" /> by
/// <see cref="Aas.IKey.Value" />'s.
/// </summary>
public static bool ReferenceKeyValuesEqual(
    Aas.IReference that,
    Aas.IReference other
)
{
    if (that.Keys.Count != other.Keys.Count)
    {
        return false;
    }

    for (int i = 0; i < that.Keys.Count; i++)
    {
        if (that.Keys[i].Value != other.Keys[i].Value)
        {
            return false;
        }
    }

    return true;
}
