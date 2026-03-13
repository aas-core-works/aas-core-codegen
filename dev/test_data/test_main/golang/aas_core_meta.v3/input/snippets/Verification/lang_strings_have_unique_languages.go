// Check that `langStrings` are specified each for a unique language.
func LangStringsHaveUniqueLanguages[L aastypes.IAbstractLangString](
	langStrings []L) bool {
	languageSet := make(map[string]struct{})

	for _, langString := range langStrings {
		language := langString.Language()
		_, has := languageSet[language]
		if has {
			return false
		}

		languageSet[language] = struct{}{}
	}

	return true
}
