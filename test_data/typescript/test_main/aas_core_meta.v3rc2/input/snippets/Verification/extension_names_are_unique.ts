/**
 * Check that all {@link types.Extension.name} are unique
 * among `extensions`.
 *
 * @param extensions - to be verified
 * @returns `true` if the check passes
 */
export function extensionNamesAreUnique(
  extensions: Iterable<AasTypes.Extension>
): boolean {
  const nameSet = new Set<string>();
  for (const extension of extensions) {
    if (nameSet.has(extension.name)) {
      return false;
    }

    nameSet.add(extension.name);
  }

  return true;
}
