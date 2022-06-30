/// <summary>
/// Check that the two references, <paramref name="that" /> and
/// <paramref name="other" />, are equal by comparing
/// their <see cref="Aas.Reference.Keys" /> by
/// <see cref="Aas.Key.Value" />'s.
/// </summary>
public static bool ReferenceKeyValuesEqual(
    Aas.Reference that,
    Aas.Reference other
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
