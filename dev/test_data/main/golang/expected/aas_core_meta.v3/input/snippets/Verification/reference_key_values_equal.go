// Check that the two references, `that` and `other`, are equal by
// comparing their [ourtypes.Reference.Keys] by [ourtypes.Key.Value]'s.
func ReferenceKeyValuesEqual(
	that ourtypes.IReference,
	other ourtypes.IReference) bool {
	thatKeys := that.Keys()
	otherKeys := other.Keys()

	if len(thatKeys) != len(otherKeys) {
		return false
	}

	for i, thatKey := range thatKeys {
		otherKey := otherKeys[i]

		if thatKey.Value() != otherKey.Value() {
			return false
		}
	}

	return true
}
