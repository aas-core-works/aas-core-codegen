/// <summary>
/// Check that <paramref name="langStrings" /> are specified each for a unique
/// language.
/// </summary>
public static bool LangStringsHaveUniqueLanguages(
    IEnumerable<Aas.IAbstractLangString> langStrings
)
{
    var languageSet = new HashSet<string>();
    foreach (var langString in langStrings)
    {
        if (languageSet.Contains(langString.Language))
        {
            return false;
        }
        languageSet.Add(langString.Language);
    }
    return true;
}
