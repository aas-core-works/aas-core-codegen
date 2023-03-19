/**
 * Check that `langStrings` are specified each for a unique
 * language.
 *
 * @param langStrings - to be verified
 * @returns `true` if the check passes
 */
export function langStringsHaveUniqueLanguages(
  langStrings: Iterable<AasTypes.IAbstractLangString>
): boolean {
  const languageSet = new Set<string>();

  for (const langString of langStrings) {
    if (languageSet.has(langString.language)) {
      return false;
    }

    languageSet.add(langString.language);
  }

  return true;
}
