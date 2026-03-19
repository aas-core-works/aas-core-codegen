def kind_or_default(self) -> "QualifierKind":
    """Return :py:attr:`kind` if set, and the default otherwise."""
    return self.kind if self.kind is not None else QualifierKind.CONCEPT_QUALIFIER
