bool QualifierTypesAreUnique(
  const std::vector<
    std::shared_ptr<types::IQualifier>
  >& qualifiers
) {
  std::set<std::wstring> type_set;
  for (const std::shared_ptr<types::IQualifier>& qualifier : qualifiers) {
    const std::wstring& type = qualifier->type();

    if (type_set.find(type) != type_set.end()) {
      return false;
    }

    type_set.insert(type);
  }

  return true;
}