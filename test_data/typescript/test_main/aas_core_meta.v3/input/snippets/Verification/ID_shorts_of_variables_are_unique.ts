/**
 * Check that all {@link types.IReferable.idShort}'s are unique
 * among `inputVariables`, `outputVariables` and `inoutputVariables`.
 *
 * @param referables - to be verified
 * @returns `true` if the check passes
 */
export function idShortsOfVariablesAreUnique(
  inputVariables: Iterable<AasTypes.IReferable> | null,
  outputVariables: Iterable<AasTypes.IReferable> | null,
  inoutputVariables: Iterable<AasTypes.IReferable> | null,
): boolean {
  const idShortSet = new Set<string>();

  for (const variable of inputVariables) {
    if (idShortSet.has(variable.idShort)) {
      return false;
    }

    idShortSet.add(variable.idShort);
  }

  for (const variable of outputVariables) {
    if (idShortSet.has(variable.idShort)) {
      return false;
    }

    idShortSet.add(variable.idShort);
  }

  for (const variable of inoutputVariables) {
    if (idShortSet.has(variable.idShort)) {
      return false;
    }

    idShortSet.add(variable.idShort);
  }

  return true;
}
