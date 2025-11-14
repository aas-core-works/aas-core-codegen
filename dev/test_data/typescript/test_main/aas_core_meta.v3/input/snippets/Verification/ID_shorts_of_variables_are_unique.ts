/**
 * Check that all {@link types.IReferable.idShort}'s are unique
 * among values of `inputVariables`, `outputVariables`
 * and `inoutputVariables`.
 *
 * @param inputVariables - to be verified
 * @param outputVariables - to be verified
 * @param inoutputVariables - to be verified
 * @returns `true` if the check passes
 */
export function idShortsOfVariablesAreUnique(
  inputVariables: Iterable<AasTypes.OperationVariable> | null,
  outputVariables: Iterable<AasTypes.OperationVariable> | null,
  inoutputVariables: Iterable<AasTypes.OperationVariable> | null,
): boolean {
  const idShortSet = new Set<string>();

  if (inputVariables !== null) {
    for (const variable of inputVariables) {
      if (variable.value.idShort !== null) {
        if (idShortSet.has(variable.value.idShort)) {
          return false;
        }

        idShortSet.add(variable.value.idShort);
      }
    }
  }

  if (outputVariables !== null) {
    for (const variable of outputVariables) {
      if (variable.value.idShort !== null) {
        if (idShortSet.has(variable.value.idShort)) {
          return false;
        }

        idShortSet.add(variable.value.idShort);
      }
    }
  }

  if (inoutputVariables !== null) {
    for (const variable of inoutputVariables) {
      if (variable.value.idShort !== null) {
        if (idShortSet.has(variable.value.idShort)) {
          return false;
        }

        idShortSet.add(variable.value.idShort);
      }
    }
  }

  return true;
}
