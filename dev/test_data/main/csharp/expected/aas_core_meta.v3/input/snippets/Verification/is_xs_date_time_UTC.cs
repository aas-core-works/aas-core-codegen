/// <summary>
/// Check that <paramref name="value" /> is a <c>xs:dateTime</c> with
/// the time zone set to UTC.
/// </summary>
public static bool IsXsDateTimeUtc(
    string value
)
{
    if (!MatchesXsDateTimeUtc(value))
    {
        return false;
    }

    return IsPrefixedWithValidDate(value);
}
