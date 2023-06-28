/// \brief Check that all the \p elements have the \p value_type.
bool PropertiesOrRangesHaveValueType(
  const std::vector<
    std::shared_ptr<types::ISubmodelElement>
  >& elements,
  types::DataTypeDefXsd value_type
);