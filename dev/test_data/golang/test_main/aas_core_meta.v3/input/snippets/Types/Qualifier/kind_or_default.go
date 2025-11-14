// Return [IQualifier.Kind] or the default value
// if it has not been set.
func (_RECEIVER_ *_STRUCT_NAME_) KindOrDefault() QualifierKind {
	v := _RECEIVER_.Kind()
	if v == nil {
		return QualifierKindConceptQualifier
	}

	return *v
}
