// Return [IReferable.Category] or the default value
// if it has not been set.
func (_RECEIVER_ *_STRUCT_NAME_) CategoryOrDefault() string {
	v := _RECEIVER_.Category()
	if v == nil {
		return "VARIABLE"
	}

	return *v
}
