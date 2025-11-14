bool ReferenceKeyValuesEqual(
  const std::shared_ptr<types::IReference>& that,
  const std::shared_ptr<types::IReference>& other
) {
  if (that->keys().size() != other->keys().size()) {
    return false;
  }

  const std::vector<
    std::shared_ptr<types::IKey>
  >& that_keys = that->keys();

  const std::vector<
    std::shared_ptr<types::IKey>
  >& other_keys = other->keys();

  for (size_t i = 0; i < that_keys.size(); ++i) {
    if (that_keys[i]->value() != other_keys[i]->value()) {
      return false;
    }
  }

  return true;
}
