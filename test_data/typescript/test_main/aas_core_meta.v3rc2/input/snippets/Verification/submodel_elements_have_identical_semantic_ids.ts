/**
 * Check that all `elements` have the identical
 * {@link types.ISubmodelElement.semanticId}.
 *
 * @param elements - to be checked
 * @returns `true` if all the semantic IDs are identical
 */
export function submodelElementsHaveIdenticalSemanticIds(
  elements: Iterable<AasTypes.ISubmodelElement>
): boolean {
  let thatSemanticId: AasTypes.Reference | null = null;
  for (const element of elements) {
    if (element.semanticId === null) {
      continue;
    }

    if (thatSemanticId === null) {
      thatSemanticId = element.semanticId;
      continue;
    }

    const thisSemanticId = element.semanticId;

    if (thisSemanticId.keys.length != thatSemanticId.keys.length) {
      return false;
    }

    for (let i = 0; i < thatSemanticId.keys.length; i++) {
      if (thisSemanticId.keys[i].value !== thatSemanticId.keys[i].value) {
        return false;
      }
    }
  }

  return true;
}
