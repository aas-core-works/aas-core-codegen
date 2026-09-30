// Check that all `elements` have the identical [ourtypes.IHasSemantics.SemanticID].
func SubmodelElementsHaveIdenticalSemanticIDs[S ourtypes.ISubmodelElement](
	elements []S) bool {
	var thatSemanticID ourtypes.IReference

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
