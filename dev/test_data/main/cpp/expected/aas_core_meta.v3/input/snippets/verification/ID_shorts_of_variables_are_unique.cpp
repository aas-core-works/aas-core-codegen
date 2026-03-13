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
) {
  std::set<std::wstring> id_short_set;
  
  if (input_variables.has_value()) {
    const std::vector<
      std::shared_ptr<types::IOperationVariable>
    >& variables = *input_variables;
    
    for (const std::shared_ptr<types::IOperationVariable>& variable : variables) {
      const common::optional<std::wstring>& id_short(
        variable->value()->id_short()
      );
      
      if (id_short.has_value()) {
        if (id_short_set.find(*id_short) != id_short_set.end()) {
          return false;
        }
        
        id_short_set.insert(*id_short);
      }
    }
  }
  
  if (output_variables.has_value()) {
    const std::vector<
      std::shared_ptr<types::IOperationVariable>
    >& variables = *output_variables;
    
    for (const std::shared_ptr<types::IOperationVariable>& variable : variables) {
      const common::optional<std::wstring>& id_short(
        variable->value()->id_short()
      );
      
      if (id_short.has_value()) {
        if (id_short_set.find(*id_short) != id_short_set.end()) {
          return false;
        }
        
        id_short_set.insert(*id_short);
      }
    }
  }
  
  if (inoutput_variables.has_value()) {
    const std::vector<
      std::shared_ptr<types::IOperationVariable>
    >& variables = *inoutput_variables;
    
    for (const std::shared_ptr<types::IOperationVariable>& variable : variables) {
      const common::optional<std::wstring>& id_short(
        variable->value()->id_short()
      );
      
      if (id_short.has_value()) {
        if (id_short_set.find(*id_short) != id_short_set.end()) {
          return false;
        }
        
        id_short_set.insert(*id_short);
      }
    }
  }

  return true;
}
