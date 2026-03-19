// Check that `elements` which are [aastypes.IProperty] or [aastypes.IRange]
// have the given `valueType`.
func PropertiesOrRangesHaveValueType[E aastypes.ISubmodelElement](
	elements []E,
	valueType aastypes.DataTypeDefXSD,
) bool {
	for _, element := range elements {
		switch element.ModelType() {
		case aastypes.ModelTypeProperty:
			prop := any(element).(aastypes.IProperty)
			if prop.ValueType() != valueType {
				return false
			}
		case aastypes.ModelTypeRange:
			rng := any(element).(aastypes.IRange)
			if rng.ValueType() != valueType {
				return false
			}
		// default passes.
		}
	}
	return true
}




































