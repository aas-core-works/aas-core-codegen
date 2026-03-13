/// \brief Check that the types::IReferable::id_short's among the \p referables are
/// unique.
template<
  typename ReferableT,
  typename std::enable_if<
    std::is_base_of<types::IReferable, ReferableT>::value
  >::type* = nullptr
>bool IdShortsAreUnique(
  const std::vector<
    std::shared_ptr<ReferableT>
  >& referables
) {
  std::set<std::wstring> id_short_set;

  for (const std::shared_ptr<types::IReferable> referable : referables) {
    const common::optional<std::wstring>& id_short = referable->id_short();

    if (id_short.has_value()) {
      if (id_short_set.find(*id_short) != id_short_set.end()) {
        return false;
      }

      id_short_set.insert(*id_short);
    }
  }

  return true;
}
