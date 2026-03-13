// Check that all `elements` have the identical [aastypes.IHasSemantics.SemanticID].
func SubmodelElementsHaveIdenticalSemanticIDs[S aastypes.ISubmodelElement](
	elements []S) bool {
	var thatSemanticID aastypes.IReference

	for _, element := range elements {
		thisSemanticID := element.SemanticID()

		if thisSemanticID == nil {
			continue
		}

		if thatSemanticID == nil {
			thatSemanticID = thisSemanticID
			continue
		}

		thisKeys := thisSemanticID.Keys()
		thatKeys := thatSemanticID.Keys()

		if len(thisKeys) != len(thatKeys) {
			return false
		}

		for i, thisKey := range thisKeys {
			thatKey := thatKeys[i]

			if thisKey.Value() != thatKey.Value() {
				return false
			}
		}
	}
	return true
}
