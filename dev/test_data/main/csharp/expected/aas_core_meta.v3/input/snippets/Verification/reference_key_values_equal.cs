/// <summary>
/// Check that the two references, <paramref name="that" /> and
/// <paramref name="other" />, are equal by comparing
/// their <see cref="Our.IReference.Keys" /> by
/// <see cref="Our.IKey.Value" />'s.
/// </summary>
public static bool ReferenceKeyValuesEqual(
    Our.IReference that,
    Our.IReference other
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
