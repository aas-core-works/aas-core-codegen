// Return [ISubmodelElementKind.OrderRelevant] or the default value
// if it has not been set.
func (_RECEIVER_ *_STRUCT_NAME_) OrderRelevantOrDefault() bool {
	v := _RECEIVER_.OrderRelevant()
	if v == nil {
		return true
	}

	return *v
}
