// Check that `elements` which are [ourtypes.IProperty] or [ourtypes.IRange]
// have the given `valueType`.
func PropertiesOrRangesHaveValueType[E ourtypes.ISubmodelElement](
	elements []E,
	valueType ourtypes.DataTypeDefXSD,
) bool {
	for _, element := range elements {
		switch element.ModelType() {
		case ourtypes.ModelTypeProperty:
			prop := any(element).(ourtypes.IProperty)
			if prop.ValueType() != valueType {
				return false
			}
		case ourtypes.ModelTypeRange:
			rng := any(element).(ourtypes.IRange)
			if rng.ValueType() != valueType {
				return false
			}
		// default passes.
		}
	}
	return true
}




































