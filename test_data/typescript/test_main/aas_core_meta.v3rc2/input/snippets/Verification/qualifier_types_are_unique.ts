/**
 * Check that there are no duplication {@link types.Qualifier.type}'s
 * in the `qualifiers`.
 *
 * @param qualifiers - to be verified
 * @returns `true` if the check passes
 */
export function qualifierTypesAreUnique(
  qualifiers: Iterable<AasTypes.Qualifier>
): boolean {
  const typeSet = new Set<string>();

  for (const qualifier of qualifiers) {
    if (typeSet.has(qualifier.type)) {
      return false;
    }

    typeSet.add(qualifier.type);
  }

  return true;
}
