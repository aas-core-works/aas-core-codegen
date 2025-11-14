// Check that the two references, `that` and `other`, are equal by
// comparing their [aastypes.Reference.Keys] by [aastypes.Key.Value]'s.
func ReferenceKeyValuesEqual(
	that aastypes.IReference,
	other aastypes.IReference) bool {
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
