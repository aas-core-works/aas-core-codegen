/**
 * Check that all {@link types.IReferable.idShort}'s are unique
 * among `referables`.
 *
 * @param referables - to be verified
 * @returns `true` if the check passes
 */
export function idShortsAreUnique(
  referables: Iterable<AasTypes.IReferable>
): boolean {
  const idShortSet = new Set<string>();
  for (const referable of referables) {
    if (referable.idShort !== null) {
      if (idShortSet.has(referable.idShort)) {
        return false;
      }

      idShortSet.add(referable.idShort);
    }
  }

  return true;
}
