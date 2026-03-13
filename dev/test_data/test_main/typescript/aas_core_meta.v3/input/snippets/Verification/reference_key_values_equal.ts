/**
 * Check that the two references, `that` and `other`,
 * are equal by comparing their {@link types.Reference.keys}
 * by {@link types.Key.value}'s.
 *
 * @param that - reference to be compared
 * @param other - to be compared against
 * @returns `true` if the key values are are equal
 */
export function referenceKeyValuesEqual(
  that: AasTypes.Reference,
  other: AasTypes.Reference
): boolean {
  if (that.keys.length != other.keys.length) {
    return false;
  }

  for (let i = 0; i < that.keys.length; i++) {
    if (that.keys[i].value !== other.keys[i].value) {
      return false;
    }
  }

  return true;
}
