def value_type_or_default(self) -> "DataTypeDefXSD":
    """Return the :py:attr:`value_type` if set, or the default otherwise."""
    return self.value_type if self.value_type is not None else DataTypeDefXSD.STRING
