// Return [IExtension.ValueType] or the default value
// if it has not been set.
func (_RECEIVER_ *_STRUCT_NAME_) ValueTypeOrDefault() DataTypeDefXSD {
	v := _RECEIVER_.ValueType()
	if v == nil {
		return DataTypeDefXSDString
	}

	return *v
}
