// Compute the volume of the box.
func (_RECEIVER_ *_STRUCT_NAME_) Volume() int64 {
	size := _RECEIVER_.Size()
	return size * size * size
}
