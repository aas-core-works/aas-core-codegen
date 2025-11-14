/// \brief Check that the run-time type of the \p element coincides with
/// \p element_type.
bool SubmodelElementIsOfType(
  const std::shared_ptr<types::ISubmodelElement>& element,
  types::AasSubmodelElements element_type
);