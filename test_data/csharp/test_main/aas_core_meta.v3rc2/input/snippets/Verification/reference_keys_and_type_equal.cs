/// <summary>
/// Check that the two references, <paramref name="that" /> and
/// <paramref name="other" />, are equal by comparing
/// their <see cref="Aas.Reference.Keys" /> and
/// <see cref="Aas.Reference.Type" />.
/// </summary>
public static bool ReferenceKeysAndTypeEqual(
    Aas.Reference that,
    Aas.Reference other
)
{
    if (that.Type != other.Type)
    {
        return false;
    }

    if (that.Keys.Count != other.Keys.Count)
    {
        return false;
    }

    for (int i = 0; i < that.Keys.Count; i++)
    {
        if (that.Keys[i].Type != other.Keys[i].Type)
        {
            return false;
        }

        if (that.Keys[i].Value != other.Keys[i].Value)
        {
            return false;
        }
    }

    return true;
}
