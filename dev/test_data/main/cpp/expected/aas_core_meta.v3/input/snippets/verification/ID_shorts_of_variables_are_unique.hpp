/// \brief Check that the types::IReferable::id_short's among all the
/// \p input_variables, \p output_variables
/// and \p inoutput_variables are unique.
bool IdShortsOfVariablesAreUnique(
  const common::optional<
    std::vector<
      std::shared_ptr<types::IOperationVariable>
    >
  >& input_variables,
  const common::optional<
    std::vector<
      std::shared_ptr<types::IOperationVariable>
    >
  >& output_variables,
  const common::optional<
    std::vector<
      std::shared_ptr<types::IOperationVariable>
    >
  >& inoutput_variables
);