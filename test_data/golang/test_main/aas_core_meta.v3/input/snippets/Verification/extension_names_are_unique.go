// Check that all [aastypes.IExtension.Name] are unique among
// `extensions`.
func ExtensionNamesAreUnique[E aastypes.IExtension](
	extensions []E) bool {
	nameSet := make(map[string]struct{})

	for _, extension := range extensions {
		name := extension.Name()
		_, has := nameSet[name]
		if has {
			return false
		}

		nameSet[name] = struct{}{}
	}
	return true
}
