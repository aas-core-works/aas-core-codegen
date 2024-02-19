/**
* Check that all elements have the identical
* {@link IHasSemantics#getSemanticId() semanticId}'s.
*/
public static boolean submodelElementsHaveIdenticalSemanticIds(
  Iterable<? extends ISubmodelElement> elements) {
  Objects.requireNonNull(elements);

  IReference thatSemanticId = null;

  for (ISubmodelElement element : elements) {
    if (!element.getSemanticId().isPresent()) {
      continue;
    }

    if (thatSemanticId == null) {
      thatSemanticId = element.getSemanticId().get();
      continue;
    }

    IReference thisSemanticId = element.getSemanticId().get();

    if (thatSemanticId.getKeys().size() != thisSemanticId.getKeys().size()) {
      return false;
    }

    for (int i = 0; i < thisSemanticId.getKeys().size(); i++) {
      if (!Objects.equals(thatSemanticId.getKeys().get(i).getValue(),
                          thisSemanticId.getKeys().get(i).getValue())) {
        return false;
      }
    }
  }

  return true;
}
