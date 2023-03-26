// Check that all [aastypes.IReferable.IDShort] are unique among
// `referables`.
func IDShortsAreUnique[R aastypes.IReferable](
	referables []R) bool {
	idShortSet := make(map[string]struct{})

	for _, referable := range referables {
		idShort := referable.IDShort()

		if idShort == nil {
			continue
		}

		_, has := idShortSet[*idShort]
		if has {
			return false
		}

		idShortSet[*idShort] = struct{}{}
	}
	return true
}
