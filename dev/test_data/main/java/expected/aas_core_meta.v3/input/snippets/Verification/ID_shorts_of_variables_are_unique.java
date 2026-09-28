/**
* Check that all {@link IReferable#getIdShort idShort} 's are among all the inputVariables, outputVariables and inoutputVariables are unique.
* @param inputVariables the inputVariables
 * @param outputVariables the outputVariables
 * @param inoutputVariables the inoutputVariables
*/
public static boolean idShortsOfVariablesAreUnique(
    Optional<List<IOperationVariable>> inputVariables,
    Optional<List<IOperationVariable>> outputVariables,
    Optional<List<IOperationVariable>> inoutputVariables) {

  Set<String> idShortSet = new HashSet<>();

  if (inputVariables.isPresent()) {
    for (IOperationVariable variable : inputVariables.get()) {
      if (variable.getValue().getIdShort().isPresent()) {
        if (idShortSet.contains(variable.getValue().getIdShort().get())) {
          return false;
        }
        idShortSet.add(variable.getValue().getIdShort().get());
      }
    }
  }

  if (outputVariables.isPresent()) {
    for (IOperationVariable variable : outputVariables.get()) {
      if (variable.getValue().getIdShort().isPresent()) {
        if (idShortSet.contains(variable.getValue().getIdShort().get())) {
          return false;
        }
        idShortSet.add(variable.getValue().getIdShort().get());
      }
    }
  }

  if (inoutputVariables.isPresent()) {
    for (IOperationVariable variable : inoutputVariables.get()) {
      if (variable.getValue().getIdShort().isPresent()) {
        if (idShortSet.contains(variable.getValue().getIdShort().get())) {
          return false;
        }
        idShortSet.add(variable.getValue().getIdShort().get());
      }
    }
  }

  return true;
}
