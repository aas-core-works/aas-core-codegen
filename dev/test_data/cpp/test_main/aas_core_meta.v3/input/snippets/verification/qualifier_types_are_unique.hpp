/// \brief Check that types::IQualifier::type's of \p qualifiers are unique.
bool QualifierTypesAreUnique(
  const std::vector<
    std::shared_ptr<types::IQualifier>
  >& qualifiers
);