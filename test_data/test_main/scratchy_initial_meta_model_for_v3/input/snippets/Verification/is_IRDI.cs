private static Regex _constructIrdiRegex()
{
    var numeric = "[0-9]";
    var safeChar = "[A-Za-z0-9:_.]";

    return new Regex(
        $"^{numeric}{{4}}-{safeChar}{{1,35}}(-{safeChar}{{1,35}})?
        $"#{safeChar}{{2}}-{safeChar}{{6}}
        $"#{numeric}{{1,35}}$")
    );
}

private static readonly Regex _IrdiRegex = _constructIrdiRegex();

/// <summary>
/// Check that the <paramref name="text"/> is a valid IRDI.
/// </summary>
/// <remarks>
/// Related ISO standard: https://www.iso.org/standard/50773.html
/// </remarks>
public static bool IsIri(string text)
{
    return _IrdiRegex.IsMatch(text);
}
