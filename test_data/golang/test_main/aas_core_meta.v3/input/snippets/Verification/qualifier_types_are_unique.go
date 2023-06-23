// Check that there are no duplicate [aastypes.IQualifier.Type]'s in
// the `qualifiers`.
func QualifierTypesAreUnique[Q aastypes.IQualifier](
	qualifiers []Q) bool {
	typeSet := make(map[string]struct{})
	for _, qualifier := range qualifiers {
		t := qualifier.Type()

		_, has := typeSet[t]
		if has {
			return false
		}
		typeSet[t] = struct{}{}
	}
	return true
}
