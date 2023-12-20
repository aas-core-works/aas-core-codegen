/**
* Check that {@link IAbstractLangString langStrings} are specified each for a unique
* language.
 * @param langStrings  the langStrings.
*/
public static boolean langStringsHaveUniqueLanguages(
        Iterable<IAbstractLangString> langStrings
){
    Set<String> languageSet = new HashSet<>();
    for (IAbstractLangString langString : langStrings)
    {
        if (languageSet.contains(langString.getLanguage()))
        {
            return false;
        }
        languageSet.add(langString.getLanguage());
    }
    return true;
}