/// \brief Check that the \p lang_strings do not have overlapping
/// types::IAbstractLangString::language's
template<
  typename LangStringT,
  typename std::enable_if<
    std::is_base_of<types::IAbstractLangString, LangStringT>::value
  >::type* = nullptr
>
bool LangStringsHaveUniqueLanguages(
  const std::vector<
    std::shared_ptr<LangStringT>
  >& lang_strings
) {
  // NOTE (mristin):
  // See: https://stackoverflow.com/questions/1349734/why-would-anyone-use-set-instead-of-unordered-set
  // For small sets, std::set is often faster than std::unordered_set.
  std::set<std::wstring> language_set;

  for (const std::shared_ptr<LangStringT>& lang_string : lang_strings) {
    const std::wstring& language = lang_string->language();

    if (language_set.find(language) != language_set.end()) {
      return false;
    }
    language_set.insert(language);
  }

  return true;
}
