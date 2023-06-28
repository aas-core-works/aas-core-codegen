bool ExtensionNamesAreUnique(
  const std::vector<
    std::shared_ptr<types::IExtension>
  >& extensions
) {
  std::set<std::wstring> name_set;

  for (const std::shared_ptr<types::IExtension>& extension : extensions) {
    const std::wstring& name = extension->name();

    if (name_set.find(name) != name_set.end()) {
      return false;
    }

    name_set.insert(name);
  }

  return true;
}
