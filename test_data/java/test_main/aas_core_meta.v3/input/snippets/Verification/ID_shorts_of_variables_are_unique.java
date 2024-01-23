/**
* Check that all {@link IReferable#getIdShort idShort} 's are among all the inputVariables, outputVariables and inoutputVariables are unique.
* @param inputVariables the inputVariables
 * @param outputVariables the outputVariables
 * @param inoutputVariables the inoutputVariables
*/
public static boolean idShortsOfVariablesAreUnique(
    Iterable<? extends IOperationVariable> inputVariables,
    Iterable<? extends IOperationVariable> outputVariables,
    Iterable<? extends IOperationVariable> inoutputVariables) {

  Set<String> idShortSet = new HashSet<>();

  if (inputVariables != null) {
    for(IOperationVariable variable : inputVariables) {
      if (variable.getValue().getIdShort().isPresent()) {
        if (idShortSet.contains(variable.getValue().getIdShort().get())) {
          return false;
        }
        idShortSet.add(variable.getValue().getIdShort().get());
      }
    }
  }

  if (outputVariables != null) {
    for (IOperationVariable variable : outputVariables) {
      if (variable.getValue().getIdShort().isPresent()) {
        if (idShortSet.contains(variable.getValue().getIdShort().get())) {
          return false;
        }
        idShortSet.add(variable.getValue().getIdShort().get());
      }
    }
  }

  if (inoutputVariables != null) {
    for (IOperationVariable variable :  inoutputVariables) {
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
