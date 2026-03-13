bool SubmodelElementsHaveIdenticalSemanticIds(
  const std::vector<
    std::shared_ptr<types::ISubmodelElement>
  >& elements
) {
  types::IReference* that_semantic_id = nullptr;

  for (const std::shared_ptr<types::ISubmodelElement>& element : elements) {
    const common::optional<
      std::shared_ptr<types::IReference>
    >& this_semantic_id(
      element->semantic_id()
    );

    if (!this_semantic_id.has_value()) {
      continue;
    }

    if (that_semantic_id == nullptr) {
      that_semantic_id = (*this_semantic_id).get();
      continue;
    }

    const std::vector<
      std::shared_ptr<types::IKey>
    >& this_keys = (*this_semantic_id)->keys();

    const std::vector<
      std::shared_ptr<types::IKey>
    >& that_keys = that_semantic_id->keys();

    if (this_keys.size() != that_keys.size()) {
      return false;
    }

    for (size_t i = 0; i < that_keys.size(); ++i) {
      if (this_keys[i]->value() != that_keys[i]->value()) {
        return false;
      }
    }
  }

  return true;
}