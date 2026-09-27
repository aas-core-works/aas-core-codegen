// Render a human-readable description of the item.
func (_RECEIVER_ *_STRUCT_NAME_) Describe() string {
	return _RECEIVER_.prefix() + " " + _RECEIVER_.Number()
}
