private static readonly Regex _idShortRe = new Regex(
    "^[a-zA-Z][a-zA-Z_0-9]*$"
);

/// <summary>
/// Check that the <paramref name="text"/> is a valid short ID.
/// </summary>
/// <remarks>
/// Related: Constraint AASd-002
/// </remarks>
public static bool IsIdShort(string text)
{
    return _idShortRe.IsMatch(text);
}
